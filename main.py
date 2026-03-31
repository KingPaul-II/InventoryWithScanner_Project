from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior

import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from collections import Counter
import os
import webbrowser
import urllib.parse
import re
import sqlite3
import time

import exporter
import database
import scanner

# ─────────────────────────────────────────
# BULLETPROOF PATH RESOLUTION
# ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "Assets")

ICON_SHARE   = os.path.join(ASSETS_DIR, "share.png")
ICON_HOME    = os.path.join(ASSETS_DIR, "home.png")
ICON_SCANNER = os.path.join(ASSETS_DIR, "scanner.png")
ICON_FLASH   = os.path.join(ASSETS_DIR, "flash.png")
ICON_FLIP    = os.path.join(ASSETS_DIR, "flip.png")

# ─────────────────────────────────────────
# WINDOW SETUP & COLOR PALETTE
# ─────────────────────────────────────────
Window.clearcolor = (0.95, 0.96, 0.97, 1)
Window.size = (400, 700)

C_BG         = (0.95, 0.96, 0.97, 1)
C_SURFACE    = (1, 1, 1, 1)            
C_PRIMARY    = (0, 0.47, 0.42, 1)      
C_PRIMARY_DK = (0, 0.30, 0.25, 1)      
C_TEXT       = (0.13, 0.13, 0.13, 1)   
C_TEXT_MUTED = (0.38, 0.38, 0.38, 1)   
C_DIVIDER    = (0.88, 0.88, 0.88, 1)   
C_DANGER     = (0.90, 0.45, 0.45, 1)   

RADIUS      = dp(14)
RADIUS_SM   = dp(10)
RADIUS_PILL = dp(26)

def is_valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

# ─────────────────────────────────────────
# CUSTOM WIDGETS
# ─────────────────────────────────────────
class IconButton(ButtonBehavior, Image):
    pass

class GreenButton(Button): 
    def __init__(self, **kwargs):
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_color', (0, 0, 0, 0))
        kwargs.setdefault('color', (1, 1, 1, 1))
        kwargs.setdefault('font_size', sp(15))
        kwargs.setdefault('bold', True)
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*C_PRIMARY)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[RADIUS_PILL])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

class GhostButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_color', (0, 0, 0, 0))
        kwargs.setdefault('color', C_PRIMARY)
        kwargs.setdefault('font_size', sp(14))
        kwargs.setdefault('bold', True)
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*C_SURFACE)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[RADIUS_PILL])
            Color(*C_PRIMARY)
            self._line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, RADIUS_PILL), width=1.4)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._line.rounded_rectangle = (self.x, self.y, self.width, self.height, RADIUS_PILL)

class DangerButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_color', (0, 0, 0, 0))
        kwargs.setdefault('color', C_DANGER)
        kwargs.setdefault('font_size', sp(14))
        kwargs.setdefault('bold', True)
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*C_SURFACE)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[RADIUS_PILL])
            Color(*C_DANGER)
            self._line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, RADIUS_PILL), width=1.4)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._line.rounded_rectangle = (self.x, self.y, self.width, self.height, RADIUS_PILL)

class StyledInput(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_color', C_SURFACE)
        kwargs.setdefault('foreground_color', C_TEXT)
        kwargs.setdefault('hint_text_color', C_TEXT_MUTED)
        kwargs.setdefault('cursor_color', C_PRIMARY)
        kwargs.setdefault('font_size', sp(15))
        kwargs.setdefault('padding', [dp(16), dp(12), dp(16), dp(12)])
        super().__init__(**kwargs)

class Divider(Widget):
    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint', (1, None))
        kwargs.setdefault('height', dp(1))
        super().__init__(**kwargs)
        with self.canvas:
            Color(*C_DIVIDER)
            self._line = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._line, 'pos', self.pos), size=lambda *_: setattr(self._line, 'size', self.size))

class StatusBadge(BoxLayout):
    def __init__(self, text, color=C_PRIMARY, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (dp(52), dp(24)))
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(color[0], color[1], color[2], 0.1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos), size=lambda *_: setattr(self._bg, 'size', self.size))
        lbl = Label(text=text, color=color, font_size=sp(12), bold=True, halign='center', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(lbl)

def show_status_popup(title, message, success=True):
    accent = C_PRIMARY if success else C_DANGER
    content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(6))
    content.add_widget(Label(text='OK' if success else '!', font_size=sp(28), bold=True, color=accent, size_hint=(1, 0.5)))
    content.add_widget(Label(text=message, color=C_TEXT, font_size=sp(13), halign='center', size_hint=(1, 0.5)))
    popup = Popup(title=title, content=content, size_hint=(0.75, 0.26), title_color=C_TEXT, title_size=sp(15), separator_color=accent, background_color=C_SURFACE)
    popup.open()
    Clock.schedule_once(lambda *_: popup.dismiss(), 2.0)

# ─────────────────────────────────────────
# SCREEN 1: HOME
# ─────────────────────────────────────────
class HomeScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        root = BoxLayout(orientation='vertical')
        with root.canvas.before:
            Color(*C_BG)
            Rectangle(pos=(0, 0), size=Window.size)

        main = BoxLayout(orientation='vertical', padding=[dp(20), dp(20), dp(20), dp(10)], spacing=dp(14), size_hint=(1, 1))

        header = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(52), spacing=dp(10))
        wordmark = BoxLayout(orientation='vertical', size_hint=(1, 1))
        
        lbl_title = Label(text='OptiStock', font_size=sp(22), bold=True, color=C_PRIMARY, halign='left', valign='bottom', size_hint=(1, 0.6))
        lbl_title.bind(size=lbl_title.setter('text_size'))
        lbl_sub = Label(text='Smart Inventory', font_size=sp(12), color=C_TEXT_MUTED, halign='left', valign='top', size_hint=(1, 0.4))
        lbl_sub.bind(size=lbl_sub.setter('text_size'))
        wordmark.add_widget(lbl_title)
        wordmark.add_widget(lbl_sub)
        header.add_widget(wordmark)
        
        btn_box = BoxLayout(size_hint=(None, 1), width=dp(60))
        if os.path.exists(ICON_SHARE):
            btn_share = IconButton(source=ICON_SHARE, size_hint=(None, None), size=(dp(30), dp(30)), pos_hint={'center_y': 0.5})
        else:
            btn_share = GhostButton(text='Share', font_size=sp(12), size_hint=(1, 0.8), pos_hint={'center_y': 0.5})
            
        btn_share.bind(on_press=lambda *_: open_global_settings())
        btn_box.add_widget(btn_share)
        header.add_widget(btn_box)
        main.add_widget(header)

        conn = sqlite3.connect(os.path.join(BASE_DIR, 'inventory.db'))
        rows = conn.execute("SELECT item_name, barcode, quantity FROM inventory ORDER BY rowid DESC LIMIT 20").fetchall()
        total_items = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
        total_qty   = conn.execute("SELECT SUM(quantity) FROM inventory").fetchone()[0] or 0
        conn.close()

        stats_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(66), spacing=dp(10))
        for label, value in [('Items', total_items), ('Total Qty', total_qty)]:
            card = FloatLayout()
            with card.canvas.before:
                Color(*C_SURFACE)
                card._bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[RADIUS_SM])
            card.bind(pos=lambda w, *_: setattr(w._bg, 'pos', w.pos), size=lambda w, *_: setattr(w._bg, 'size', w.size))
            card.add_widget(Label(text=str(value), font_size=sp(20), bold=True, color=C_PRIMARY, pos_hint={'center_x': 0.5, 'center_y': 0.62}))
            card.add_widget(Label(text=label, font_size=sp(11), color=C_TEXT_MUTED, pos_hint={'center_x': 0.5, 'center_y': 0.22}))
            stats_row.add_widget(card)
        main.add_widget(stats_row)

        lbl_recent = Label(text='Recently Scanned', font_size=sp(15), color=C_TEXT_MUTED, halign='left', valign='middle', size_hint=(1, None), height=dp(24))
        lbl_recent.bind(size=lbl_recent.setter('text_size'))
        main.add_widget(lbl_recent)

        scroll = ScrollView(size_hint=(1, 1), bar_width=0)
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(7))
        list_box.bind(minimum_height=list_box.setter('height'))

        for r in rows:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(58), padding=[dp(14), dp(6), dp(14), dp(6)], spacing=dp(10))
            with row.canvas.before:
                Color(*C_SURFACE)
                row._bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[RADIUS_SM])
            row.bind(pos=lambda w, *_: setattr(w._bg, 'pos', w.pos), size=lambda w, *_: setattr(w._bg, 'size', w.size))
            
            dot = Label(text='•', font_size=sp(14), color=C_PRIMARY, size_hint=(None, 1), width=dp(15))
            
            text_col = BoxLayout(orientation='vertical', size_hint=(1, 1), spacing=0)
            name_lbl = Label(text=r[0], font_size=sp(14), color=C_TEXT, halign='left', valign='bottom', size_hint=(1, 0.6))
            name_lbl.bind(size=name_lbl.setter('text_size'))
            bc_lbl = Label(text=str(r[1]), font_size=sp(11), color=C_TEXT_MUTED, halign='left', valign='top', size_hint=(1, 0.4))
            bc_lbl.bind(size=bc_lbl.setter('text_size'))
            text_col.add_widget(name_lbl)
            text_col.add_widget(bc_lbl)
            
            badge = StatusBadge(text=f'x{r[2]}', pos_hint={'center_y': 0.5})
            row.add_widget(dot); row.add_widget(text_col); row.add_widget(badge)
            list_box.add_widget(row)

        if not rows:
            list_box.add_widget(Label(text='No items yet. Start scanning!', color=C_TEXT_MUTED, font_size=sp(14), size_hint_y=None, height=dp(60)))

        scroll.add_widget(list_box)
        main.add_widget(scroll)
        root.add_widget(main)

        bot_nav = FloatLayout(size_hint=(1, None), height=dp(90))
        with bot_nav.canvas.before:
            Color(*C_SURFACE)
            self.bot_rect = Rectangle(pos=bot_nav.pos, size=bot_nav.size)
        bot_nav.bind(pos=lambda w, *_: setattr(self.bot_rect, 'pos', w.pos), size=lambda w, *_: setattr(self.bot_rect, 'size', w.size))

        scan_container = FloatLayout(size_hint=(None, None), size=(dp(64), dp(64)), pos_hint={'center_x': 0.5, 'center_y': 0.6})
        with scan_container.canvas.before:
            Color(*C_PRIMARY)
            self.scan_circ = Ellipse(pos=scan_container.pos, size=scan_container.size)
        scan_container.bind(pos=lambda w, *_: setattr(self.scan_circ, 'pos', w.pos), size=lambda w, *_: setattr(self.scan_circ, 'size', w.size))

        if os.path.exists(ICON_SCANNER):
            scan_btn = IconButton(source=ICON_SCANNER, size_hint=(0.55, 0.55), pos_hint={'center_x': 0.5, 'center_y': 0.5}, color=(1,1,1,1))
        else:
            scan_btn = Button(text="[+]", font_size=sp(30), background_normal='', background_color=(0,0,0,0), bold=True, color=(1,1,1,1))
            
        scan_btn.bind(on_press=self._go_scan)
        scan_container.add_widget(scan_btn)
        bot_nav.add_widget(scan_container)
        
        root.add_widget(bot_nav)
        self.add_widget(root)

    def _go_scan(self, *_):
        self.manager.transition = SlideTransition(direction='left', duration=0.25)
        self.manager.current = 'scanner'

# ─────────────────────────────────────────
# SCREEN 2: SCANNER 
# ─────────────────────────────────────────
class ScannerScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.is_manual_open = False
        self.scan_buffer = []
        self._scanning_enabled = False 

        root = FloatLayout()
        self.img = Image(size_hint=(1, 1), fit_mode="contain", pos_hint={'center_x': 0.5, 'center_y': 0.5})
        root.add_widget(self.img)

        top_bar = FloatLayout(size_hint=(1, None), height=dp(56), pos_hint={'top': 1})
        with top_bar.canvas.before:
            Color(1, 1, 1, 0.85)
            top_bar._bg = Rectangle(pos=top_bar.pos, size=top_bar.size)
        top_bar.bind(pos=lambda w, *_: setattr(w._bg, 'pos', w.pos), size=lambda w, *_: setattr(w._bg, 'size', w.size))

        btn_back = Button(text='<', font_size=sp(24), bold=True, background_normal='', background_color=(0, 0, 0, 0), color=C_TEXT, size_hint=(None, 1), width=dp(40), pos_hint={'x': 0.02, 'center_y': 0.5})
        btn_back.bind(on_press=lambda *_: self._go_back())
        
        lbl_title = Label(text='Scan Barcode', font_size=sp(16), bold=True, color=C_TEXT, size_hint=(None, 1), width=dp(150), pos_hint={'center_x': 0.5, 'center_y': 0.5}, halign='center')
        
        btn_manual = GhostButton(text='Manual', size_hint=(None, 0.65), width=dp(76), pos_hint={'right': 0.96, 'center_y': 0.5})
        btn_manual.bind(on_press=self.toggle_dropdown)

        top_bar.add_widget(btn_back)
        top_bar.add_widget(lbl_title)
        top_bar.add_widget(btn_manual)
        root.add_widget(top_bar)

        self.drawer = BoxLayout(orientation='horizontal', size_hint=(1, None), height=0, opacity=0, pos_hint={'x': 0, 'top': 0.92}, padding=[dp(10), dp(6)], spacing=dp(8))
        with self.drawer.canvas.before:
            Color(*C_SURFACE)
            self._drawer_bg = Rectangle(pos=self.drawer.pos, size=self.drawer.size)
        self.drawer.bind(pos=lambda w, *_: setattr(self._drawer_bg, 'pos', w.pos), size=lambda w, *_: setattr(self._drawer_bg, 'size', w.size))
        self.manual_input = StyledInput(hint_text='Enter barcode number...', multiline=False, size_hint=(0.72, 1))
        btn_go = GreenButton(text='Go', size_hint=(0.28, 0.85), pos_hint={'center_y': 0.5})
        btn_go.bind(on_press=self.run_manual_search)
        self.drawer.add_widget(self.manual_input); self.drawer.add_widget(btn_go)
        root.add_widget(self.drawer)

        reticle = RelativeLayout(size_hint=(None, None), size=(dp(230), dp(130)), pos_hint={'center_x': 0.5, 'center_y': 0.55})
        with reticle.canvas:
            Color(*C_PRIMARY, 0.9)
            t, arm = dp(2.5), dp(20)
            w, h = dp(230), dp(130)
            Rectangle(pos=(0, h - arm), size=(t, arm)); Rectangle(pos=(0, h - t), size=(arm, t))
            Rectangle(pos=(w - t, h - arm), size=(t, arm)); Rectangle(pos=(w - arm, h - t), size=(arm, t))
            Rectangle(pos=(0, 0), size=(t, arm)); Rectangle(pos=(0, 0), size=(arm, t))
            Rectangle(pos=(w - t, 0), size=(t, arm)); Rectangle(pos=(w - arm, 0), size=(arm, t))
        root.add_widget(reticle)

        bot_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(80), pos_hint={'x': 0, 'y': 0}, padding=[dp(20), dp(10)])
        with bot_bar.canvas.before:
            Color(1, 1, 1, 0.85)
            bot_bar._bg = Rectangle(pos=bot_bar.pos, size=bot_bar.size)
        bot_bar.bind(pos=lambda w, *_: setattr(w._bg, 'pos', w.pos), size=lambda w, *_: setattr(w._bg, 'size', w.size))

        if os.path.exists(ICON_FLASH):
            btn_flash = IconButton(source=ICON_FLASH, size_hint=(None, None), size=(dp(30), dp(30)), pos_hint={'center_y': 0.5}, color=C_TEXT)
        else:
            btn_flash = Button(text='⚡', font_size=sp(24), background_normal='', background_color=(0,0,0,0), color=C_TEXT, size_hint=(None, 0.6), width=dp(55), pos_hint={'center_y': 0.5})

        if os.path.exists(ICON_FLIP):
            btn_flip = IconButton(source=ICON_FLIP, size_hint=(None, None), size=(dp(34), dp(34)), pos_hint={'center_y': 0.5}, color=C_TEXT)
        else:
            btn_flip = Button(text='⟳', font_size=sp(28), background_normal='', background_color=(0,0,0,0), color=C_TEXT, size_hint=(None, 0.6), width=dp(55), pos_hint={'center_y': 0.5})

        status_box = BoxLayout(orientation='vertical')
        self.lbl_status = Label(text='Warming up scanner...', font_size=sp(13), color=C_TEXT, halign='center')
        self.lbl_dots = Label(text='', font_size=sp(18), color=C_PRIMARY, halign='center')
        status_box.add_widget(self.lbl_status); status_box.add_widget(self.lbl_dots)

        bot_bar.add_widget(btn_flash); bot_bar.add_widget(status_box); bot_bar.add_widget(btn_flip)
        root.add_widget(bot_bar)

        self.add_widget(root)

        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cam_event = Clock.schedule_interval(self.update_camera, 1.0 / 30.0)

        self.warmup_event = Clock.schedule_once(self._activate_scanner, 1.2)

    def _activate_scanner(self, dt):
        self._scanning_enabled = True
        if hasattr(self, 'lbl_status'):
            self.lbl_status.text = 'Point camera at a barcode'

    def toggle_dropdown(self, *_):
        target_h  = dp(52) if not self.is_manual_open else 0
        target_op = 1      if not self.is_manual_open else 0
        Animation(height=target_h, opacity=target_op, duration=0.20).start(self.drawer)
        self.is_manual_open = not self.is_manual_open

    def run_manual_search(self, *_):
        bc = self.manual_input.text.strip()
        if bc:
            app = App.get_running_app()
            app.scanned_barcode = bc
            
            if hasattr(app, 'last_scan_path') and os.path.exists(app.last_scan_path):
                try: os.remove(app.last_scan_path)
                except: pass
            app.last_scan_path = ''
            
            self._scanning_enabled = False
            self.manager.current = 'details'

    def on_leave(self):
        if hasattr(self, 'warmup_event'):
            self.warmup_event.cancel()
        self.cam_event.cancel()
        if self.capture:
            self.capture.release()

    def _go_back(self):
        self.manager.transition = SlideTransition(direction='right', duration=0.25)
        self.manager.current = 'home'

    def update_camera(self, dt):
        ret, frame = self.capture.read()
        if not ret: return

        if self._scanning_enabled and not self.is_manual_open:
            fh, fw = frame.shape[:2]
            cx, cy = fw // 2, fh // 2
            
            bw, bh = 400, 300 
            sx, sy = max(0, cx - bw // 2), max(0, cy - bh // 2)
            ex, ey = min(fw, cx + bw // 2), min(fh, cy + bh // 2)
            
            target_area = frame[sy:ey, sx:ex]
            
            gray = cv2.cvtColor(target_area, cv2.COLOR_BGR2GRAY)

            fast_symbols = [ZBarSymbol.EAN13, ZBarSymbol.UPCA]
            barcodes = pyzbar.decode(gray, symbols=fast_symbols)

            if barcodes:
                barcode_data = barcodes[0].data.decode('utf-8')
                
                if len(barcode_data) in [8, 12, 13] and barcode_data.isdigit():
                    self.scan_buffer.append(barcode_data)
                    
                    if len(self.scan_buffer) > 6:
                        self.scan_buffer.pop(0)
                    
                    winner_tally = Counter(self.scan_buffer).most_common(1)[0]
                    winner_barcode = winner_tally[0]
                    winner_count = winner_tally[1]

                    n = min(winner_count, 3)
                    self.lbl_dots.text   = 'o ' * n + '. ' * (3 - n)
                    self.lbl_status.text = 'Hold steady...'

                    if winner_count >= 3:
                        
                        bw_thumb, bh_thumb = 400, 250
                        sx_t, sy_t = max(0, cx - bw_thumb // 2), max(0, cy - bh_thumb // 2)
                        ex_t, ey_t = min(fw, cx + bw_thumb // 2), min(fh, cy + bh_thumb // 2)
                        thumb_area = frame[sy_t:ey_t, sx_t:ex_t]
                        
                        app = App.get_running_app()
                        if hasattr(app, 'last_scan_path') and os.path.exists(app.last_scan_path):
                            try: os.remove(app.last_scan_path)
                            except: pass
                        
                        scan_filename = f'scan_{int(time.time() * 1000)}.png'
                        app.last_scan_path = os.path.join(BASE_DIR, scan_filename)
                        cv2.imwrite(app.last_scan_path, thumb_area)
                        
                        app.scanned_barcode = winner_barcode
                        self.scan_buffer.clear()
                        self._scanning_enabled = False
                        self.manager.current = 'details'
                        return
            else:
                self.lbl_status.text = 'Point camera at a barcode'

        buf = cv2.flip(frame, 0).tobytes()
        tex = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        tex.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img.texture = tex


# ─────────────────────────────────────────
# SCREEN 3: DETAILS 
# ─────────────────────────────────────────
class DetailsScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.qty_val = 1
        
        app = App.get_running_app()
        barcode = app.scanned_barcode

        root = FloatLayout()
        with root.canvas.before:
            Color(*C_BG)
            Rectangle(pos=(0, 0), size=Window.size)

        main = BoxLayout(orientation='vertical', padding=[dp(20), dp(44), dp(20), dp(20)], spacing=dp(14), size_hint=(1, 1))

        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(48))
        btn_back = Button(text='< Back', font_size=sp(14), background_normal='', background_color=(0, 0, 0, 0), color=C_PRIMARY, halign='left', size_hint=(0.35, 1))
        btn_back.bind(on_press=lambda *_: setattr(self.manager, 'current', 'scanner'))
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text='Update Inventory', font_size=sp(16), bold=True, color=C_TEXT, size_hint=(0.65, 1)))
        main.add_widget(top_bar)

        img_path = getattr(app, 'last_scan_path', '')
        if img_path and os.path.exists(img_path):
            img_box = BoxLayout(size_hint=(1, None), height=dp(150))
            with img_box.canvas.before:
                Color(0.92, 0.94, 0.96, 1) 
                img_box._bg = RoundedRectangle(pos=img_box.pos, size=img_box.size, radius=[RADIUS])
            img_box.bind(pos=lambda w, *_: setattr(w._bg, 'pos', w.pos), size=lambda w, *_: setattr(w._bg, 'size', w.size))
            img_box.add_widget(Image(source=img_path, fit_mode="contain"))
            main.add_widget(img_box)

        chip_row = BoxLayout(size_hint=(1, None), height=dp(32))
        chip = BoxLayout(size_hint=(None, 1), width=dp(210), padding=[dp(12), 0])
        with chip.canvas.before:
            Color(0.9, 0.92, 0.94, 1) 
            chip._bg = RoundedRectangle(pos=chip.pos, size=chip.size, radius=[dp(16)])
        chip.bind(pos=lambda w, *_: setattr(w._bg, 'pos', w.pos), size=lambda w, *_: setattr(w._bg, 'size', w.size))
        chip.add_widget(Label(text=f'# {barcode}', font_size=sp(12), color=C_TEXT_MUTED))
        chip_row.add_widget(chip); main.add_widget(chip_row)

        main.add_widget(Label(text='Item Name', font_size=sp(11), color=C_TEXT_MUTED, halign='left', text_size=(Window.width - dp(40), None), size_hint=(1, None), height=dp(20)))
        local_name = scanner.check_local_db(barcode) or scanner.lookup_barcode_online(barcode) or ''
        self.name_in = StyledInput(text=local_name, hint_text='Enter or confirm item name...', multiline=False, size_hint=(1, None), height=dp(48))
        main.add_widget(self.name_in)

        main.add_widget(Label(text='Quantity Adjustment', font_size=sp(11), color=C_TEXT_MUTED, halign='left', text_size=(Window.width - dp(40), None), size_hint=(1, None), height=dp(20)))
        qty_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(52), spacing=dp(10))
        btn_minus = GhostButton(text='-', font_size=sp(22), size_hint=(None, 1), width=dp(52))
        self.qty_lbl = Label(text='1', font_size=sp(24), bold=True, color=C_TEXT, size_hint=(1, 1))
        btn_plus = GreenButton(text='+', font_size=sp(22), size_hint=(None, 1), width=dp(52))
        btn_minus.bind(on_press=lambda *_: self._change_qty(-1))
        btn_plus.bind(on_press=lambda *_: self._change_qty(1))
        qty_row.add_widget(btn_minus); qty_row.add_widget(self.qty_lbl); qty_row.add_widget(btn_plus)
        main.add_widget(qty_row)

        main.add_widget(Widget())

        action_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(54), spacing=dp(10))
        btn_remove = DangerButton(text='REMOVE', size_hint=(0.4, 1))
        btn_remove.bind(on_press=lambda *_: self.process_item('remove'))
        btn_add = GreenButton(text='ADD STOCK', size_hint=(0.6, 1))
        btn_add.bind(on_press=lambda *_: self.process_item('add'))
        
        action_row.add_widget(btn_remove)
        action_row.add_widget(btn_add)
        main.add_widget(action_row)

        root.add_widget(main)
        self.add_widget(root)

    def _change_qty(self, delta):
        self.qty_val = max(1, self.qty_val + delta)
        self.qty_lbl.text = str(self.qty_val)

    def process_item(self, mode):
        name = self.name_in.text.strip()
        if not name:
            show_status_popup('Error', 'Please enter an item name.', success=False)
            return

        barcode = App.get_running_app().scanned_barcode
        final_qty = self.qty_val

        if mode == 'remove':
            conn = sqlite3.connect(os.path.join(BASE_DIR, 'inventory.db'))
            res = conn.execute("SELECT quantity FROM inventory WHERE barcode=?", (barcode,)).fetchone()
            conn.close()
            current_stock = res[0] if res else 0

            if current_stock - self.qty_val < 0:
                show_status_popup('Error', 'Cannot remove more than in stock!', success=False)
                return
            final_qty = -self.qty_val 

        database.add_or_update_item(barcode, name, final_qty)
        
        self.manager.transition = SlideTransition(direction='left', duration=0.25)
        self.manager.current = 'update'


# ─────────────────────────────────────────
# SCREEN 4: SUCCESS / EXPORT 
# ─────────────────────────────────────────
class UpdateScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        root = FloatLayout()
        with root.canvas.before:
            Color(*C_BG)
            Rectangle(pos=(0, 0), size=Window.size)

        main = BoxLayout(orientation='vertical', padding=[dp(28), dp(50), dp(28), dp(28)], spacing=dp(16), size_hint=(1, 1))

        tick_wrap = FloatLayout(size_hint=(1, None), height=dp(90))
        inner = BoxLayout(size_hint=(None, None), size=(dp(72), dp(72)), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        with inner.canvas.before:
            Color(0, 0.47, 0.42, 0.15) 
            inner._ell = Ellipse(pos=inner.pos, size=inner.size)
        inner.bind(pos=lambda w, *_: setattr(w._ell, 'pos', w.pos), size=lambda w, *_: setattr(w._ell, 'size', w.size))
        inner.add_widget(Label(text='OK', font_size=sp(22), bold=True, color=C_PRIMARY))
        tick_wrap.add_widget(inner); main.add_widget(tick_wrap)

        main.add_widget(Label(text='Database Updated!', font_size=sp(26), bold=True, color=C_TEXT, size_hint=(1, None), height=dp(36), halign='center'))
        main.add_widget(Label(text='Inventory processed successfully.', font_size=sp(13), color=C_TEXT_MUTED, size_hint=(1, None), height=dp(24), halign='center'))

        main.add_widget(Divider())

        main.add_widget(Label(text='EXPORT', font_size=sp(11), color=C_TEXT_MUTED, halign='left', text_size=(Window.width - dp(56), None), size_hint=(1, None), height=dp(26)))

        btn_xl = GreenButton(text='Export to Excel', size_hint=(1, None), height=dp(50))
        btn_xl.bind(on_press=lambda *_: [exporter.export_to_excel(), show_status_popup('Saved', 'Excel report created.')])
        btn_txt = GhostButton(text='Export to Text', size_hint=(1, None), height=dp(50))
        btn_txt.bind(on_press=lambda *_: [exporter.export_to_text(), show_status_popup('Saved', 'Text summary created.')])
        main.add_widget(btn_xl); main.add_widget(btn_txt)

        main.add_widget(Widget())

        nav = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(50), spacing=dp(10))

        if os.path.exists(ICON_SHARE):
            btn_share = IconButton(source=ICON_SHARE, size_hint=(0.20, 1), color=C_TEXT)
        else:
            btn_share = GhostButton(text='Share', font_size=sp(12), size_hint=(0.25, 1))
        btn_share.bind(on_press=lambda *_: open_global_settings())

        btn_again = GhostButton(text='Scan Again', size_hint=(0.50, 1))
        btn_again.bind(on_press=lambda *_: [setattr(self.manager, 'transition', SlideTransition(direction='right')), setattr(self.manager, 'current', 'scanner')])

        if os.path.exists(ICON_HOME):
            btn_home = IconButton(source=ICON_HOME, size_hint=(0.25, 1), color=C_TEXT)
        else:
            btn_home = Button(text='⌂', font_size=sp(28), background_normal='', background_color=(0,0,0,0), color=C_TEXT, size_hint=(0.25, 1))
            
        btn_home.bind(on_press=lambda *_: [setattr(self.manager, 'transition', SlideTransition(direction='right')), setattr(self.manager, 'current', 'home')])

        nav.add_widget(btn_share); nav.add_widget(btn_again); nav.add_widget(btn_home)
        main.add_widget(nav)

        root.add_widget(main)
        self.add_widget(root)

# ─────────────────────────────────────────
# APP & EMAIL LOGIC 
# ─────────────────────────────────────────
class OptiStockApp(App):
    def build(self):
        database.create_db()
        
        try:
            conn = sqlite3.connect(os.path.join(BASE_DIR, 'inventory.db'))
            conn.execute("DELETE FROM inventory WHERE barcode='9370055677023'")
            conn.commit()
            conn.close()
        except Exception:
            pass
            
        self.scanned_barcode = ''
        self.last_scan_path = ''
        
        sm = ScreenManager(transition=SlideTransition(duration=0.25))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ScannerScreen(name='scanner'))
        sm.add_widget(DetailsScreen(name='details'))
        sm.add_widget(UpdateScreen(name='update'))
        return sm

def open_global_settings():
    content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
    content.add_widget(Label(text='Recipient Email', font_size=sp(12), color=C_TEXT_MUTED, halign='left', size_hint=(1, None), height=dp(22)))
    email_in = StyledInput(hint_text='you@dlsu.edu.ph', multiline=False, size_hint=(1, None), height=dp(46))
    content.add_widget(email_in)

    btns = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint=(1, None), height=dp(46))
    popup = Popup(title='Share Report', content=content, size_hint=(0.88, 0.36), title_color=C_TEXT, title_size=sp(15), separator_color=C_PRIMARY, background_color=C_SURFACE)

    def attempt_send(mode):
        email = email_in.text.strip()
        if not is_valid_email(email):
            show_status_popup('Error', 'Enter a valid email.', success=False)
            return
        trigger_email_intent(email, mode)
        popup.dismiss()
        show_status_popup('Success', 'Email client opened!')

    b_txt = GhostButton(text='Text', size_hint=(0.4, 1))
    b_txt.bind(on_press=lambda *_: attempt_send('text'))
    b_xl = GreenButton(text='Excel', size_hint=(0.6, 1))
    b_xl.bind(on_press=lambda *_: attempt_send('excel'))
    btns.add_widget(b_txt); btns.add_widget(b_xl); content.add_widget(btns)
    popup.open()

def trigger_email_intent(recipient, mode):
    content = "Inventory Report Attached"
    if platform != 'android':
        sub  = urllib.parse.quote(f'OptiStock Report - {mode.upper()}')
        body = urllib.parse.quote(content)
        webbrowser.open(f'mailto:{recipient}?subject={sub}&body={body}')

if __name__ == '__main__':
    OptiStockApp().run()
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

# --- ADD THIS NEW IMPORT ---
from kivy.uix.behaviors import ButtonBehavior

import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import time
from collections import Counter
import os

# Import your helper files
import exporter
import database
import scanner

# Set global app background to White
Window.clearcolor = (0.95, 0.95, 0.95, 1)
Window.size = (400, 700)

GREEN = (0.18, 0.49, 0.20, 1)
DARK_GREEN = (0.10, 0.35, 0.12, 1)
WHITE = (1, 1, 1, 1)
BLACK = (0.1, 0.1, 0.1, 1)

class IconButton(ButtonBehavior, Image):
    """A custom widget that turns any PNG into a clickable button without ugly borders."""
    pass

class GreenVaultApp(App):
    def build(self):
        database.create_db()
        self.scanned_barcode = ""
        self.scanned_item_name = ""
        
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ScannerScreen(name='scanner'))
        sm.add_widget(DetailsScreen(name='details'))
        sm.add_widget(UpdateScreen(name='update'))
        return sm

# ==========================================
# SCREEN 1: HOME SCREEN (MOCKUP LIST UI)
# ==========================================
from kivy.graphics import Color, Rectangle, Line, Ellipse

class HomeScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=0, spacing=0)

        # --- Top Bar ---
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=70, padding=[15, 10])
        
        with top_bar.canvas.before:
            Color(1, 1, 1, 1) 
            self.top_rect = Rectangle(size=top_bar.size, pos=top_bar.pos)
        
        with top_bar.canvas.after:
            Color(0, 0, 0, 1) 
            self.top_line = Rectangle(size=(top_bar.width, 1), pos=(top_bar.x, top_bar.y))
            
        top_bar.bind(size=self._update_top_bar, pos=self._update_top_bar)
        top_bar.add_widget(Widget(size_hint=(None, 1), width=40))
        
        title = Label(text="GREEN VAULT", color=GREEN, font_size='28sp', bold=True, halign="center", valign="middle", size_hint=(1, 1))
        title.bind(size=title.setter('text_size')) 
        top_bar.add_widget(title)
        
        if os.path.exists("Assets/setting.png"):
            btn_settings = IconButton(source="Assets/setting.png", size_hint=(None, 1), width=40, color=BLACK)
        else:
            btn_settings = Button(text="*", font_size='30sp', size_hint=(None, 1), width=40, background_normal='', background_color=(0,0,0,0), color=BLACK)
        btn_settings.bind(on_press=self.open_settings)
        top_bar.add_widget(btn_settings)
        
        layout.add_widget(top_bar)

        # --- Main Content Area ---
        content_area = BoxLayout(orientation='vertical', padding=20, spacing=10)

        header_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=50)
        recent_lbl = Label(text="Recent Scans", color=BLACK, font_size='22sp', bold=True, halign="left", size_hint=(1, 0.8))
        recent_lbl.bind(size=recent_lbl.setter('text_size'))
        header_box.add_widget(recent_lbl)
        
        line_widget = Widget(size_hint=(1, 0.2)) 
        with line_widget.canvas.before:
            Color(0.8, 0.8, 0.8, 1)
            self.recent_line = Rectangle(size=(line_widget.width, 2), pos=(line_widget.x, line_widget.y))
        line_widget.bind(size=self._update_recent_line, pos=self._update_recent_line)
        header_box.add_widget(line_widget)
        
        content_area.add_widget(header_box)
        
        # --- THE NEW LIST DB FETCH ---
        import sqlite3
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        # We now ask for the barcode too!
        cursor.execute("SELECT item_name, barcode, quantity FROM inventory ORDER BY rowid DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            empty_lbl = Label(text="No items yet. Start scanning!", color=(0.5, 0.5, 0.5, 1), size_hint=(1, 1), halign="center", valign="middle")
            empty_lbl.bind(size=empty_lbl.setter('text_size'))
            content_area.add_widget(empty_lbl)
        else:
            scroll = ScrollView(size_hint=(1, 1))
            recent_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
            recent_list.bind(minimum_height=recent_list.setter('height'))
            
            # --- THE NEW LIST ITEM UI ---
            # Helper function to create bulletproof separator lines inside our loop
            def create_separator():
                sep = Widget(size_hint=(1, None), height=1)
                with sep.canvas.before:
                    Color(0.85, 0.85, 0.85, 1) # Light gray
                    rect = Rectangle(pos=sep.pos, size=sep.size)
                def update_rect(instance, value):
                    rect.pos = instance.pos
                    rect.size = instance.size
                sep.bind(pos=update_rect, size=update_rect)
                return sep

            for row in rows:
                name, barcode, qty = row[0], row[1], row[2]
                
                # The container for ONE list item (Height 65 allows room for 2 lines + line)
                item_container = BoxLayout(orientation='vertical', size_hint_y=None, height=65, padding=[5, 5, 5, 0])
                
                info_row = BoxLayout(orientation='horizontal')
                
                # LEFT SIDE: Name & Barcode
                left_col = BoxLayout(orientation='vertical', size_hint_x=0.7)
                lbl_name = Label(text=str(name), color=BLACK, font_size='16sp', bold=True, halign='left', valign='bottom')
                lbl_name.bind(size=lbl_name.setter('text_size'))
                
                lbl_barcode = Label(text=str(barcode), color=(0.5, 0.5, 0.5, 1), font_size='13sp', halign='left', valign='top')
                lbl_barcode.bind(size=lbl_barcode.setter('text_size'))
                
                left_col.add_widget(lbl_name)
                left_col.add_widget(lbl_barcode)
                
                # RIGHT SIDE: Quantity
                lbl_qty = Label(text=f"Qty: {qty}", color=GREEN, font_size='16sp', bold=True, halign='right', valign='middle', size_hint_x=0.3)
                lbl_qty.bind(size=lbl_qty.setter('text_size'))
                
                info_row.add_widget(left_col)
                info_row.add_widget(lbl_qty)
                
                item_container.add_widget(info_row)
                item_container.add_widget(Widget(size_hint_y=None, height=5)) # Tiny spacer
                item_container.add_widget(create_separator()) # Add the gray line
                
                recent_list.add_widget(item_container)
                
            scroll.add_widget(recent_list)
            content_area.add_widget(scroll)
        
        layout.add_widget(content_area)

        # --- Bottom Bar ---
        bot_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=100)
        
        with bot_bar.canvas.before:
            Color(1, 1, 1, 1) 
            self.bot_rect = Rectangle(size=bot_bar.size, pos=bot_bar.pos)
        
        with bot_bar.canvas.after:
            Color(0, 0, 0, 1) 
            self.bot_line = Rectangle(size=(bot_bar.width, 1), pos=(bot_bar.x, bot_bar.top - 1))
            
        bot_bar.bind(size=self._update_bot_bar, pos=self._update_bot_bar)

        bot_bar.add_widget(Widget()) 
        
        cam_container = BoxLayout(size_hint=(None, None), size=(80, 80), pos_hint={'center_y': 0.5})
        with cam_container.canvas.before:
            Color(*GREEN) 
            self.cam_circle = Ellipse(size=cam_container.size, pos=cam_container.pos)
            Color(0, 0, 0, 1) 
            self.cam_circle_border = Line(ellipse=(cam_container.x, cam_container.y, cam_container.width, cam_container.height), width=1.5)
        cam_container.bind(size=self._update_cam_circle, pos=self._update_cam_circle)

        if os.path.exists("Assets/scanner.png"):
            cam_icon = IconButton(source="Assets/scanner.png", size_hint=(0.5, 0.5), pos_hint={'center_x': 0.5, 'center_y': 0.5}, color=BLACK)
        else:
            cam_icon = Button(text="Scan", background_normal='', background_color=(0,0,0,0), color=BLACK)
            
        def go_to_scanner(instance):
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'scanner'
        cam_icon.bind(on_press=go_to_scanner)
        
        cam_container.add_widget(cam_icon)
        bot_bar.add_widget(cam_container)
        bot_bar.add_widget(Widget()) 
        
        layout.add_widget(bot_bar)
        self.add_widget(layout)

    # --- Canvas Update Helpers ---
    def _update_top_bar(self, instance, value):
        self.top_rect.pos = instance.pos
        self.top_rect.size = instance.size
        self.top_line.pos = (instance.x, instance.y)
        self.top_line.size = (instance.width, 1) 
        
    def _update_recent_line(self, instance, value):
        self.recent_line.pos = (instance.x, instance.y)
        self.recent_line.size = (instance.width, 2)
        
    def _update_bot_bar(self, instance, value):
        self.bot_rect.pos = instance.pos
        self.bot_rect.size = instance.size
        self.bot_line.pos = (instance.x, instance.top - 1)
        self.bot_line.size = (instance.width, 1) 
        
    def _update_cam_circle(self, instance, value):
        self.cam_circle.pos = instance.pos
        self.cam_circle.size = instance.size
        self.cam_circle_border.ellipse = (instance.x, instance.y, instance.width, instance.height)
        
    def open_settings(self, instance):
        content = BoxLayout(orientation='vertical', padding=[20, 20, 20, 10], spacing=15)
        lbl_info = Label(text="Export your local inventory\ndata via email attachment.", color=BLACK, halign='center', valign='middle', font_size='16sp', size_hint=(1, 0.4))
        lbl_info.bind(size=lbl_info.setter('text_size'))
        content.add_widget(lbl_info)

        btn_email = Button(text="Send to Gmail", font_size='18sp', bold=True, background_normal='', background_color=GREEN, color=WHITE, size_hint=(1, 0.4))
        content.add_widget(btn_email)

        lbl_exit = Label(text="(Tap anywhere outside this box to exit)", color=(0.5, 0.5, 0.5, 1), font_size='13sp', halign='center', valign='bottom', size_hint=(1, 0.2))
        content.add_widget(lbl_exit)

        popup = Popup(title="Settings", title_color=GREEN, title_size='22sp', separator_color=GREEN, content=content, size_hint=(0.85, 0.4), background='', background_color=(1, 1, 1, 1))
        
        with popup.canvas.after:
            Color(0.2, 0.2, 0.2, 1) 
            popup.border_line = Line(width=1.5, rectangle=(popup.x, popup.y, popup.width, popup.height))
            
        def update_popup_border(inst, value):
            inst.border_line.rectangle = (inst.x, inst.y, inst.width, inst.height)
            
        popup.bind(pos=update_popup_border, size=update_popup_border)
        btn_email.bind(on_press=lambda x: [trigger_email_intent(), popup.dismiss()])
        popup.open()

# ==========================================
# SCREEN 2: SCANNER SCREEN (BULLETPROOF LINES)
# ==========================================
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

class ScannerScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.is_manual_open = False # Track if the dropdown is open
        
        # FloatLayout lets us layer the UI perfectly over the background
        self.layout = FloatLayout()
        
        # --- 1. BASE LAYER: Camera & Bottom Bar ---
        self.base_layout = BoxLayout(orientation='vertical')
        
        # Spacer: Pushes the camera down so it sits under the Top Bar & Tab
        self.base_layout.add_widget(Widget(size_hint_y=None, height=85))
        
        # Camera Feed (Using fit_mode="contain" to avoid warnings!)
        self.img = Image(size_hint=(1, 1), fit_mode="contain")
        self.base_layout.add_widget(self.img)
        
        # --- THE UPGRADED BOTTOM BAR ---
        self.bot_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=80, padding=10)
        
        with self.bot_bar.canvas.before:
            Color(1, 1, 1, 1) # White Background
            self.bot_rect = Rectangle(size=self.bot_bar.size, pos=self.bot_bar.pos)
            Color(0, 0, 0, 1) # Thin Black Top Line
            # THE FIX: 1-pixel solid rectangle instead of Line
            self.bot_line = Rectangle(size=(self.bot_bar.width, 1), pos=(self.bot_bar.x, self.bot_bar.top - 1))
        self.bot_bar.bind(size=self._update_bot_bar, pos=self._update_bot_bar)

        self.bot_bar.add_widget(Widget()) # Ghost spacer (Left)
        
        # Flash Icon
        if os.path.exists("Assets/flash.png"):
            btn_flash = IconButton(source="Assets/flash.png", size_hint=(None, 0.6), width=45, pos_hint={'center_y': 0.5}, color=BLACK)
        else:
            btn_flash = Button(text="Flash", background_normal='', background_color=DARK_GREEN)
            
        # Flip Icon
        if os.path.exists("Assets/flip.png"):
            btn_flip = IconButton(source="Assets/flip.png", size_hint=(None, 0.7), width=55, pos_hint={'center_y': 0.5}, color=BLACK)
        else:
            btn_flip = Button(text="Flip", background_normal='', background_color=DARK_GREEN)

        self.bot_bar.add_widget(btn_flash)
        self.bot_bar.add_widget(Widget(size_hint=(None, 1), width=100)) # Center gap between icons
        self.bot_bar.add_widget(btn_flip)
        self.bot_bar.add_widget(Widget()) # Ghost spacer (Right)
        
        self.base_layout.add_widget(self.bot_bar)
        self.layout.add_widget(self.base_layout)
        
        # --- 2. OVERLAY LAYER: The Dropdown UI ---
        # This sits at the very top of the screen and grows downwards
        self.overlay = BoxLayout(orientation='vertical', size_hint=(1, None), pos_hint={'top': 1})
        self.overlay.bind(minimum_height=self.overlay.setter('height'))
        
        # Part A: The fixed Top Bar (White with black bottom border)
        self.top_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=60, padding=[10, 0])
        
        with self.top_bar.canvas.before:
            Color(1, 1, 1, 1) # White Background
            self.top_rect = Rectangle(size=self.top_bar.size, pos=self.top_bar.pos)
            
        with self.top_bar.canvas.after:
            Color(0, 0, 0, 1) # Thin Black Border Line
            # THE FIX: 1-pixel solid rectangle instead of Line
            self.top_line = Rectangle(size=(self.top_bar.width, 1), pos=(self.top_bar.x, self.top_bar.y))
            
        self.top_bar.bind(size=self._update_top_rect, pos=self._update_top_rect)
        
        # --- RETURN ICON FIX ---
        if os.path.exists("Assets/return.png"):
            btn_back = IconButton(source="Assets/return.png", size_hint=(0.15, 0.6), pos_hint={'center_y': 0.5}, color=BLACK)
        else:
            btn_back = Button(text="<", background_normal='', background_color=(0,0,0,0), color=BLACK, font_size='24sp', bold=True, size_hint=(0.15, 1))

        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        
        lbl_title = Label(text="Enter Barcode manually?", color=BLACK, bold=True, halign="center", font_size='18sp', size_hint=(0.70, 1))
        
        spacer_right = Widget(size_hint=(0.15, 1)) # The invisible balance weight!
        
        self.top_bar.add_widget(btn_back)
        self.top_bar.add_widget(lbl_title)
        self.top_bar.add_widget(spacer_right)
        self.overlay.add_widget(self.top_bar)
        
        # Part B: The Sliding Input Area
        self.slide_area = BoxLayout(orientation='horizontal', size_hint=(1, None), height=0, opacity=0, padding=[10, 5, 10, 5], spacing=10)
        
        with self.slide_area.canvas.before:
            Color(1, 1, 1, 1)
            self.slide_rect = Rectangle(size=self.slide_area.size, pos=self.slide_area.pos)
            
        with self.slide_area.canvas.after:
            Color(0, 0, 0, 1) 
            # THE FIX: 1-pixel solid rectangle instead of Line
            self.slide_line = Rectangle(size=(self.slide_area.width, 1), pos=(self.slide_area.x, self.slide_area.y))
            
        self.slide_area.bind(size=self._update_slide_rect, pos=self._update_slide_rect)
        
        self.manual_input = TextInput(hint_text="Barcode #", multiline=False, size_hint=(0.7, 1), font_size='16sp')
        self.manual_search = Button(text="Search", background_normal='', background_color=GREEN, size_hint=(0.3, 1))
        self.manual_search.bind(on_press=self.run_manual_search)
        
        self.slide_area.add_widget(self.manual_input)
        self.slide_area.add_widget(self.manual_search)
        self.overlay.add_widget(self.slide_area)
        
        # Part C: The Green Pull-Tab
        self.tab_area = BoxLayout(orientation='horizontal', size_hint=(1, None), height=25)
        self.tab_area.add_widget(Widget()) # Empty space left
        
        self.btn_tab = Button(text="v", background_normal='', background_color=DARK_GREEN, color=WHITE, font_size='18sp', bold=True, size_hint=(None, 1), width=100)
        self.btn_tab.bind(on_press=self.toggle_dropdown)
        
        self.tab_area.add_widget(self.btn_tab)
        self.tab_area.add_widget(Widget()) # Empty space right
        
        self.overlay.add_widget(self.tab_area)
        self.layout.add_widget(self.overlay)
        self.add_widget(self.layout)

        # Camera Logic
        self.capture = cv2.VideoCapture(0)
        self.scan_buffer = []
        self.frame_counter = 0
        self.last_barcode_rect = None 
        self.box_memory_frames = 0    
        self.cam_event = Clock.schedule_interval(self.update_camera, 1.0/30.0)

    # --- UI Canvas Update Helpers (Now with Rectangles!) ---
    def _update_top_rect(self, instance, value):
        self.top_rect.pos = instance.pos
        self.top_rect.size = instance.size
        if not self.is_manual_open:
            self.top_line.pos = (instance.x, instance.y)
            self.top_line.size = (instance.width, 1)
        else:
            self.top_line.size = (0, 0) # Hide it when dropdown opens

    def _update_slide_rect(self, instance, value):
        self.slide_rect.pos = instance.pos
        self.slide_rect.size = instance.size
        if self.is_manual_open:
            self.slide_line.pos = (instance.x, instance.y)
            self.slide_line.size = (instance.width, 1)
        else:
            self.slide_line.size = (0, 0) # Hide it when dropdown closes

    def _update_bot_bar(self, instance, value):
        self.bot_rect.pos = instance.pos
        self.bot_rect.size = instance.size
        self.bot_line.pos = (instance.x, instance.top - 1)
        self.bot_line.size = (instance.width, 1)

    # --- Dropdown Logic ---
    def toggle_dropdown(self, instance):
        if not self.is_manual_open:
            self.is_manual_open = True
            self.btn_tab.text = "^"
            self.slide_area.height = 55
            self.slide_area.opacity = 1
        else:
            self.is_manual_open = False
            self.btn_tab.text = "v"
            self.slide_area.height = 0
            self.slide_area.opacity = 0
            self.manual_input.text = "" 
            
        self._update_top_rect(self.top_bar, None)
        self._update_slide_rect(self.slide_area, None)

    def run_manual_search(self, instance):
        if self.manual_input.text:
            app = App.get_running_app()
            app.scanned_barcode = self.manual_input.text
            self.manual_input.text = "" 
            self.toggle_dropdown(None) 
            self.manager.transition = SlideTransition(direction='up')
            self.manager.current = 'details'

    def on_leave(self):
        self.cam_event.cancel()
        self.capture.release()

    def update_camera(self, dt):
        ret, frame = self.capture.read()
        if not ret: return

        h, w, _ = frame.shape
        target_w = int(h * 0.75) 
        start_x = (w - target_w) // 2
        frame = frame[:, start_x:start_x+target_w]

        self.frame_counter += 1
        
        # PAUSE SCANNING if the user is typing!
        if self.frame_counter % 5 == 0 and not self.is_manual_open: 
            barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.UPCA, ZBarSymbol.UPCE])
            if not barcodes:
                self.last_barcode_rect = None

            for barcode in barcodes:
                self.last_barcode_rect = barcode.rect
                self.box_memory_frames = 5 
                self.scan_buffer.append(barcode.data.decode("utf-8"))
                break 
            
            if len(self.scan_buffer) >= 3:
                winner_barcode = Counter(self.scan_buffer).most_common(1)[0][0]
                if self.last_barcode_rect:
                    x, y, w, h = self.last_barcode_rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 5)
                
                cv2.imwrite("last_scan.png", frame) 
                
                app = App.get_running_app()
                app.scanned_barcode = winner_barcode
                self.manager.transition = SlideTransition(direction='up')
                self.manager.current = 'details'
                return

        if self.last_barcode_rect and self.box_memory_frames > 0:
            x, y, w, h = self.last_barcode_rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
            self.box_memory_frames -= 1

        buf1 = cv2.flip(frame, 0)
        buf = buf1.tobytes()
        image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img.texture = image_texture

# ==========================================
# SCREEN 3: ITEM DETAILS SCREEN (FORM LAYOUT)
# ==========================================
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle

class DetailsScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        barcode = app.scanned_barcode
        
        layout = FloatLayout()
        
        with layout.canvas.before:
            Color(0.95, 0.95, 0.95, 1) 
            self.bg_rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_bg_rect, pos=self._update_bg_rect)
        
        content_box = BoxLayout(orientation='vertical', padding=[20, 10, 20, 20], spacing=10, size_hint=(1, 0.95), pos_hint={'top': 0.95})
        
        with content_box.canvas.before:
            Color(1, 1, 1, 1) 
            self.sheet_rect = RoundedRectangle(size=content_box.size, pos=content_box.pos, radius=[40, 40, 0, 0])
        content_box.bind(size=self._update_sheet_rect, pos=self._update_sheet_rect)

        # --- 1. Downward Chevron Button ---
        btn_down = Button(size_hint=(1, 0.1), background_normal='', background_color=(0,0,0,0))
        def slide_down_back(instance):
            self.manager.transition = SlideTransition(direction='down')
            self.manager.current = 'scanner'
        btn_down.bind(on_press=slide_down_back)
        
        with btn_down.canvas.after:
            Color(*GREEN)
            self.chevron_line1 = Line(points=[], width=2)
            self.chevron_line2 = Line(points=[], width=2)
            self.chevron_line3 = Line(points=[], width=2)
            self.chevron_line4 = Line(points=[], width=2)
        btn_down.bind(size=self._update_chevron, pos=self._update_chevron)
        content_box.add_widget(btn_down)

        # --- 2. Title & Image ---
        content_box.add_widget(Label(text="Add to Inventory?", color=BLACK, font_size='24sp', bold=True, size_hint=(1, 0.1)))

        if os.path.exists("last_scan.png"):
            content_box.add_widget(Image(source="last_scan.png", size_hint=(1, 0.35)))
        
        # --- 3. ALIGNED FORM SECTION ---
        
        lbl_barcode = Label(
            text=f"[b]Barcode:[/b] {barcode}", 
            markup=True,
            color=BLACK, font_size='16sp', 
            size_hint=(1, None), height=30, 
            halign='center', valign='middle'
        )
        lbl_barcode.bind(size=lbl_barcode.setter('text_size'))
        content_box.add_widget(lbl_barcode)
        
        # --- ROW 1: Name ---
        local_name = scanner.check_local_db(barcode)
        if not local_name:
            local_name = scanner.lookup_barcode_online(barcode)

        row1 = BoxLayout(orientation='horizontal', size_hint=(1, None), height=45, spacing=10)
        lbl_name = Label(text="Name:", color=GREEN, font_size='18sp', bold=True, size_hint=(0.35, 1), halign='left', valign='middle')
        lbl_name.bind(size=lbl_name.setter('text_size'))
        row1.add_widget(lbl_name)

        name_container = BoxLayout(size_hint=(0.65, 1))
        with name_container.canvas.before:
            Color(*GREEN)
            self.name_border = Line(rectangle=(name_container.x, name_container.y, name_container.width, name_container.height), width=1)
        name_container.bind(size=self._update_name_border, pos=self._update_name_border)
        
        self.name_input = TextInput(
            text=local_name if local_name else "", 
            background_normal='', background_active='', background_color=(1,1,1,1),
            foreground_color=BLACK, 
            multiline=False, padding=[10, 12], font_size='16sp'
        )
        name_container.add_widget(self.name_input)
        row1.add_widget(name_container)
        content_box.add_widget(row1)

        # --- ROW 2: Stock (Uneditable Text) ---
        import sqlite3
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute("SELECT quantity FROM inventory WHERE barcode=?", (barcode,))
        res = c.fetchone()
        current_stock = res[0] if res else 0
        conn.close()

        row2 = BoxLayout(orientation='horizontal', size_hint=(1, None), height=30, spacing=10)
        lbl_stock_title = Label(text="Stock:", color=GREEN, font_size='18sp', bold=True, size_hint=(0.35, 1), halign='left', valign='middle')
        lbl_stock_title.bind(size=lbl_stock_title.setter('text_size'))
        row2.add_widget(lbl_stock_title)

        # THE FIX: Added padding=[10, 0] to shift it exactly 10 pixels right, and font_size='16sp' to match the input boxes!
        lbl_stock_val = Label(text=str(current_stock), color=BLACK, font_size='16sp', bold=True, size_hint=(0.65, 1), halign='left', valign='middle', padding=[10, 0])
        lbl_stock_val.bind(size=lbl_stock_val.setter('text_size'))
        row2.add_widget(lbl_stock_val)
        content_box.add_widget(row2)
        
        # --- ROW 3: Qty to Add ---
        row3 = BoxLayout(orientation='horizontal', size_hint=(1, None), height=45, spacing=10)
        lbl_qty = Label(text="Qty to Add:", color=GREEN, font_size='18sp', bold=True, size_hint=(0.35, 1), halign='left', valign='middle')
        lbl_qty.bind(size=lbl_qty.setter('text_size'))
        row3.add_widget(lbl_qty)

        qty_container = BoxLayout(size_hint=(0.65, 1))
        with qty_container.canvas.before:
            Color(*GREEN)
            self.qty_border = Line(rectangle=(qty_container.x, qty_container.y, qty_container.width, qty_container.height), width=1)
        qty_container.bind(size=self._update_qty_border, pos=self._update_qty_border)
        
        self.qty_input = TextInput(
            text="", input_filter='int',
            background_normal='', background_active='', background_color=(1,1,1,1),
            foreground_color=BLACK, 
            multiline=False, padding=[10, 12], font_size='16sp'
        )
        qty_container.add_widget(self.qty_input)
        row3.add_widget(qty_container)
        content_box.add_widget(row3)

        # Spacer
        content_box.add_widget(Widget(size_hint=(1, 0.05)))

        # --- ADD Button ---
        fl_btn = FloatLayout(size_hint=(1, 0.15))
        
        btn_add = Button(text="ADD", bold=True, size_hint=(0.5, None), height=50, pos_hint={'center_x': 0.5, 'center_y': 0.5}, background_normal='', background_color=(0,0,0,0), color=WHITE)
        with btn_add.canvas.before:
            Color(*GREEN)
            self.add_rect = RoundedRectangle(size=btn_add.size, pos=btn_add.pos, radius=[15])
        btn_add.bind(size=self._update_add_rect, pos=self._update_add_rect)
        btn_add.bind(on_press=self.save_item)
        
        fl_btn.add_widget(btn_add)
        content_box.add_widget(fl_btn)
        
        layout.add_widget(content_box)
        self.add_widget(layout)

    # --- Canvas Update Helpers ---
    def _update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_sheet_rect(self, instance, value):
        self.sheet_rect.pos = instance.pos
        self.sheet_rect.size = instance.size

    def _update_chevron(self, instance, value):
        cx = instance.center_x
        cy = instance.center_y + 5
        w = 30
        h = 10
        self.chevron_line1.points = [cx - w, cy + h, cx, cy]
        self.chevron_line2.points = [cx, cy, cx + w, cy + h]
        self.chevron_line3.points = [cx - w, cy + h + 8, cx, cy + 8]
        self.chevron_line4.points = [cx, cy + 8, cx + w, cy + h + 8]

    def _update_name_border(self, instance, value):
        self.name_border.rectangle = (instance.x, instance.y, instance.width, instance.height)

    def _update_qty_border(self, instance, value):
        self.qty_border.rectangle = (instance.x, instance.y, instance.width, instance.height)
        
    def _update_add_rect(self, instance, value):
        self.add_rect.pos = instance.pos
        self.add_rect.size = instance.size

    def save_item(self, instance):
        app = App.get_running_app()
        qty = int(self.qty_input.text) if self.qty_input.text else 1
        name = self.name_input.text if self.name_input.text else "Unnamed Item"
        
        database.add_or_update_item(app.scanned_barcode, name, qty)
        
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'update'


# ==========================================
# SCREEN 4: UPDATE INVENTORY (PIXEL-PERFECT MOCKUP)
# ==========================================
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle

class UpdateScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        
        # Main wrapper
        layout = FloatLayout()
        
        # --- MAIN CONTENT ---
        # Increased top padding to push "Item Added" down slightly to match mockup
        content = BoxLayout(orientation='vertical', padding=[30, 90, 30, 0], spacing=25, size_hint=(1, 1))
        
        # 1. Title
        lbl_title = Label(text="Item Added!", color=GREEN, font_size='34sp', bold=True, size_hint=(1, None), height=60)
        content.add_widget(lbl_title)
        
        # 2. Divider Line
        line_container = BoxLayout(size_hint=(0.8, None), height=2, pos_hint={'center_x': 0.5})
        with line_container.canvas.before:
            Color(0.7, 0.7, 0.7, 1) # Grey
            self.line_rect = Rectangle(size=line_container.size, pos=line_container.pos)
        line_container.bind(size=self._update_line_rect, pos=self._update_line_rect)
        content.add_widget(line_container)
        
        # 3. Export Subtitle
        lbl_export = Label(text="Export", color=BLACK, font_size='18sp', bold=True, size_hint=(1, None), height=40, halign="left", valign="middle")
        lbl_export.bind(size=lbl_export.setter('text_size'))
        content.add_widget(lbl_export)
        
        # 4. EXCEL BUTTON
        btn_excel = Button(text="Excel", font_size='20sp', bold=True, background_normal='', background_color=(0,0,0,0), color=WHITE, size_hint=(0.6, None), height=55, pos_hint={'center_x': 0.5})
        with btn_excel.canvas.before:
            Color(*GREEN)
            self.excel_rect = RoundedRectangle(radius=[15])
        btn_excel.bind(size=self._update_excel_rect, pos=self._update_excel_rect)
        btn_excel.bind(on_press=lambda x: self.export_with_feedback('excel'))
        content.add_widget(btn_excel)
        
        # 5. TEXT BUTTON
        btn_text = Button(text="Text", font_size='20sp', bold=True, background_normal='', background_color=(0,0,0,0), color=GREEN, size_hint=(0.6, None), height=55, pos_hint={'center_x': 0.5})
        with btn_text.canvas.before:
            Color(1, 1, 1, 1) # White fill
            self.text_rect_bg = RoundedRectangle(radius=[15])
            Color(*GREEN) # Green border
            self.text_rect_line = Line(rounded_rectangle=[0,0,0,0,15], width=2)
        btn_text.bind(size=self._update_text_rect, pos=self._update_text_rect)
        btn_text.bind(on_press=lambda x: self.export_with_feedback('text'))
        content.add_widget(btn_text)
        
        # 6. GIANT INVISIBLE SPACER (The Spring)
        content.add_widget(Widget(size_hint=(1, 1))) 
        
        layout.add_widget(content)
        
        # --- BOTTOM NAVIGATION BAR ---
        # Increased height from 80 to 110 to fit the bigger icons
        nav_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=110, padding=20, pos_hint={'y': 0})
        
        with nav_bar.canvas.before:
            Color(1, 1, 1, 1)
            self.nav_rect = Rectangle(size=nav_bar.size, pos=nav_bar.pos)
        nav_bar.bind(size=self._update_nav_rect, pos=self._update_nav_rect)

        nav_bar.add_widget(Widget()) # Left spacer
        
        # 1. Settings Icon (Scaled Up)
        if os.path.exists("Assets/setting.png"):
            btn_settings = IconButton(source="Assets/setting.png", size_hint=(None, 1), width=65, color=BLACK)
        else:
            btn_settings = Button(text="Set", background_normal='', background_color=(0,0,0,0), color=BLACK)
        btn_settings.bind(on_press=self.open_settings)
        
        # 2. Home Icon (Scaled Up)
        if os.path.exists("Assets/home.png"):
            btn_home = IconButton(source="Assets/home.png", size_hint=(None, 1), width=70, color=BLACK)
        else:
            btn_home = Button(text="Home", background_normal='', background_color=(0,0,0,0), color=BLACK)
        def go_home(instance):
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = 'home'
        btn_home.bind(on_press=go_home)
        
        # 3. Scanner Icon (Scaled Up WITH GREEN CIRCLE)
        # We put it inside a container to draw the green ring around it
        scan_container = BoxLayout(size_hint=(None, None), size=(80, 80), pos_hint={'center_y': 0.5})
        with scan_container.canvas.before:
            Color(*GREEN) # Green ring color
            self.scan_circle = Line(ellipse=(scan_container.x, scan_container.y, scan_container.width, scan_container.height), width=2.5)
        scan_container.bind(size=self._update_scan_circle, pos=self._update_scan_circle)

        if os.path.exists("Assets/scanner.png"):
            # Size hint 0.6 keeps the icon slightly smaller than the ring for nice padding
            btn_scan = IconButton(source="Assets/scanner.png", size_hint=(0.6, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5}, color=BLACK)
        else:
            btn_scan = Button(text="Scan", background_normal='', background_color=(0,0,0,0), color=BLACK)
            
        def go_scan(instance):
            self.manager.transition = SlideTransition(direction='down')
            self.manager.current = 'scanner'
        btn_scan.bind(on_press=go_scan)
        
        scan_container.add_widget(btn_scan)
        
        # Add everything to the Nav Bar
        nav_bar.add_widget(btn_settings)
        nav_bar.add_widget(Widget())
        nav_bar.add_widget(btn_home)
        nav_bar.add_widget(Widget())
        nav_bar.add_widget(scan_container) # Add the container, not just the button!
        nav_bar.add_widget(Widget()) # Right spacer
        
        layout.add_widget(nav_bar)
        self.add_widget(layout)

    # --- Canvas Update Helpers ---
    def _update_line_rect(self, instance, value):
        self.line_rect.pos = instance.pos
        self.line_rect.size = instance.size
        
    def _update_excel_rect(self, instance, value):
        self.excel_rect.pos = instance.pos
        self.excel_rect.size = instance.size
        
    def _update_text_rect(self, instance, value):
        self.text_rect_bg.pos = instance.pos
        self.text_rect_bg.size = instance.size
        self.text_rect_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, 15]

    def _update_nav_rect(self, instance, value):
        self.nav_rect.pos = instance.pos
        self.nav_rect.size = instance.size

    def _update_scan_circle(self, instance, value):
        self.scan_circle.ellipse = (instance.x, instance.y, instance.width, instance.height)

    # --- Export Feedback Popup ---
    def export_with_feedback(self, exp_type):
        if exp_type == 'excel':
            exporter.export_to_excel()
            msg = "Excel Exported!"
        else:
            exporter.export_to_text()
            msg = "Text Exported!"
            
        content = Label(text=msg, color=WHITE, font_size='18sp', bold=True)
        popup = Popup(title="", separator_height=0, content=content, size_hint=(0.6, 0.1), background_color=GREEN, background='atlas://data/images/defaulttheme/button_pressed')
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)

    def open_settings(self, instance):
        content = BoxLayout(orientation='vertical', padding=[20, 20, 20, 10], spacing=15)
        
        lbl_info = Label(
            text="Export your local inventory\ndata via email attachment.", 
            color=BLACK, 
            halign='center', 
            valign='middle',
            font_size='16sp',
            size_hint=(1, 0.4)
        )
        lbl_info.bind(size=lbl_info.setter('text_size'))
        content.add_widget(lbl_info)

        btn_email = Button(
            text="Send to Gmail", 
            font_size='18sp', 
            bold=True, 
            background_normal='', 
            background_color=GREEN, 
            color=WHITE, 
            size_hint=(1, 0.4)
        )
        content.add_widget(btn_email)

        lbl_exit = Label(
            text="(Tap anywhere outside this box to exit)", 
            color=(0.5, 0.5, 0.5, 1), 
            font_size='13sp', 
            halign='center', 
            valign='bottom',
            size_hint=(1, 0.2)
        )
        content.add_widget(lbl_exit)

        popup = Popup(
            title="Settings", 
            title_color=GREEN,
            title_size='22sp',
            separator_color=GREEN,
            content=content, 
            size_hint=(0.85, 0.4),
            background='',                  # <--- THE FIX: Removes the blue texture!
            background_color=(1, 1, 1, 1)   # <--- Leaves it pure white!
        )
        
        with popup.canvas.after:
            Color(0.2, 0.2, 0.2, 1) 
            popup.border_line = Line(width=1.5, rectangle=(popup.x, popup.y, popup.width, popup.height))
            
        def update_popup_border(inst, value):
            inst.border_line.rectangle = (inst.x, inst.y, inst.width, inst.height)
            
        popup.bind(pos=update_popup_border, size=update_popup_border)

        btn_email.bind(on_press=lambda x: [trigger_email_intent(), popup.dismiss()])
        popup.open()

# ==========================================
# GMAIL INTENT HELPER
# ==========================================
def trigger_email_intent():
    inventory_data = ""
    if os.path.exists("Inventory_Summary.txt"):
        with open("Inventory_Summary.txt", "r") as f:
            inventory_data = f.read()
    else:
        inventory_data = "No inventory data found. Please run the exporter first."

    if platform == 'android':
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        String = autoclass('java.lang.String')

        intent = Intent(Intent.ACTION_SEND)
        intent.setType("message/rfc822") 
        intent.putExtra(Intent.EXTRA_SUBJECT, cast('java.lang.CharSequence', String("Green Vault Inventory Report")))
        intent.putExtra(Intent.EXTRA_TEXT, cast('java.lang.CharSequence', String(inventory_data)))

        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
        currentActivity.startActivity(Intent.createChooser(intent, cast('java.lang.CharSequence', String("Send Inventory via:"))))
    else:
        print("\n--- 📧 SIMULATING EMAIL INTENT ON WINDOWS ---")
        print("Subject: Green Vault Inventory Report")
        print(f"Body:\n{inventory_data}")
        print("-------------------------------------------\n")

if __name__ == "__main__":
    GreenVaultApp().run()

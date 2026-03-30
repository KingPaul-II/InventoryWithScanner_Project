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
# SCREEN 1: HOME SCREEN
# ==========================================
class HomeScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Top Bar
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        title = Label(text="GREEN VAULT", color=GREEN, font_size='28sp', bold=True, halign="left")
        btn_settings = Button(text="Settings", font_size='16sp', size_hint=(0.3, 1), background_normal='', background_color=WHITE, color=BLACK)
        btn_settings.bind(on_press=self.open_settings)
        top_bar.add_widget(title)
        top_bar.add_widget(btn_settings)
        layout.add_widget(top_bar)

        # Recent Scans
        layout.add_widget(Label(text="Recent Scans", color=BLACK, font_size='18sp', bold=True, size_hint=(1, 0.05)))
        
        scroll = ScrollView(size_hint=(1, 0.65))
        recent_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        recent_list.bind(minimum_height=recent_list.setter('height'))
        
        import sqlite3
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT item_name, quantity FROM inventory ORDER BY rowid DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            recent_list.add_widget(Label(text="No items yet. Start scanning!", color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=40))
        for row in rows:
            item_lbl = Label(text=f"{row[0]} (Qty: {row[1]})", color=BLACK, size_hint_y=None, height=30)
            recent_list.add_widget(item_lbl)
            
        scroll.add_widget(recent_list)
        layout.add_widget(scroll)

        # Bottom Button
        btn_scan = Button(text="OPEN SCANNER", font_size='20sp', bold=True, background_normal='', background_color=GREEN, color=WHITE, size_hint=(1, 0.15))
        def go_to_scanner(instance):
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'scanner'
        btn_scan.bind(on_press=go_to_scanner)
        layout.add_widget(btn_scan)

        self.add_widget(layout)

    def open_settings(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        btn_email = Button(text="Send Inventory to Gmail", background_normal='', background_color=GREEN)
        content.add_widget(btn_email)
        popup = Popup(title="Settings", content=content, size_hint=(0.8, 0.3))
        btn_email.bind(on_press=lambda x: [trigger_email_intent(), popup.dismiss()])
        popup.open()


# ==========================================
# SCREEN 2: SCANNER SCREEN (PERFECTLY CENTERED TEXT)
# ==========================================
from kivy.graphics import Color, Rectangle, Line
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
        
        # Camera Feed (keep_ratio prevents stretching!)
        self.img = Image(size_hint=(1, 1), keep_ratio=True, allow_stretch=True)
        self.base_layout.add_widget(self.img)
        
        # The Bottom Bar
        self.bot_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=60, padding=10, spacing=10)
        self.bot_bar.add_widget(Button(text="Flash", background_normal='', background_color=DARK_GREEN))
        self.bot_bar.add_widget(Button(text="Flip Cam", background_normal='', background_color=DARK_GREEN))
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
            self.top_line = Line(points=[self.top_bar.x, self.top_bar.y, self.top_bar.right, self.top_bar.y], width=1)
            
        self.top_bar.bind(size=self._update_top_rect, pos=self._update_top_rect)
        
        # PERFECT CENTERING FIX: Left (15%) + Center (70%) + Right (15%)
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
            self.slide_line = Line(points=[self.slide_area.x, self.slide_area.y, self.slide_area.right, self.slide_area.y], width=1)
            
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

    # --- UI Canvas Update Helpers ---
    def _update_top_rect(self, instance, value):
        self.top_rect.pos = instance.pos
        self.top_rect.size = instance.size
        if not self.is_manual_open:
            self.top_line.points = [instance.x, instance.y, instance.right, instance.y]
        else:
            self.top_line.points = [0,0,0,0]

    def _update_slide_rect(self, instance, value):
        self.slide_rect.pos = instance.pos
        self.slide_rect.size = instance.size
        if self.is_manual_open:
            self.slide_line.points = [instance.x, instance.y, instance.right, instance.y]
        else:
            self.slide_line.points = [0,0,0,0]

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
        
        # PAUSE SCANNING if the user is typing![cite: 7]
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
# SCREEN 3: ITEM DETAILS SCREEN
# ==========================================
class DetailsScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        barcode = app.scanned_barcode
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Top Slide-Down Button
        btn_down = Button(text="v Return to Scanner", background_normal='', background_color=WHITE, color=BLACK, size_hint=(1, 0.1))
        def slide_down_back(instance):
            self.manager.transition = SlideTransition(direction='down')
            self.manager.current = 'scanner'
        btn_down.bind(on_press=slide_down_back)
        layout.add_widget(btn_down)

        layout.add_widget(Label(text="Add to Inventory?", color=BLACK, font_size='22sp', bold=True, size_hint=(1, 0.1)))

        if os.path.exists("last_scan.png"):
            layout.add_widget(Image(source="last_scan.png", size_hint=(1, 0.3)))
        
        layout.add_widget(Label(text=f"Barcode: {barcode}", color=BLACK, font_size='18sp', size_hint=(1, 0.05)))
        
        local_name = scanner.check_local_db(barcode)
        if not local_name:
            local_name = scanner.lookup_barcode_online(barcode)

        if local_name:
            self.name_input = TextInput(text=local_name, multiline=False, size_hint=(1, 0.1))
        else:
            self.name_input = TextInput(hint_text="Unknown! Enter Product Name...", background_color=(1, 0.9, 0.8, 1), multiline=False, size_hint=(1, 0.1))
        layout.add_widget(self.name_input)

        import sqlite3
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute("SELECT quantity FROM inventory WHERE barcode=?", (barcode,))
        res = c.fetchone()
        current_stock = res[0] if res else 0
        conn.close()

        layout.add_widget(Label(text=f"Current Stock: {current_stock}", color=BLACK, font_size='18sp', size_hint=(1, 0.05)))
        
        self.qty_input = TextInput(hint_text="How many to add?", input_filter='int', font_size='20sp', halign='center', multiline=False, size_hint=(1, 0.1))
        layout.add_widget(self.qty_input)

        btn_add = Button(text="ADD", background_normal='', background_color=GREEN, bold=True, size_hint=(1, 0.15))
        btn_add.bind(on_press=self.save_item)
        layout.add_widget(btn_add)
        
        self.add_widget(layout)

    def save_item(self, instance):
        app = App.get_running_app()
        qty = int(self.qty_input.text) if self.qty_input.text else 1
        name = self.name_input.text if self.name_input.text else "Unnamed Item"
        
        database.add_or_update_item(app.scanned_barcode, name, qty)
        
        # Slide LEFT to the success screen
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'update'


# ==========================================
# SCREEN 4: UPDATE INVENTORY (SUCCESS)
# ==========================================
class UpdateScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        layout.add_widget(Label(text="ADDED!", color=GREEN, font_size='40sp', bold=True, size_hint=(1, 0.3)))

        btn_excel = Button(text="Export Excel", background_normal='', background_color=GREEN, font_size='20sp', size_hint=(1, 0.2))
        btn_excel.bind(on_press=lambda x: exporter.export_to_excel())
        layout.add_widget(btn_excel)

        btn_text = Button(text="Export Text", background_normal='', background_color=DARK_GREEN, font_size='20sp', size_hint=(1, 0.2))
        btn_text.bind(on_press=lambda x: exporter.export_to_text())
        layout.add_widget(btn_text)

        # --- Bottom Nav (Matches Sketch) ---
        nav = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.2))
        
        btn_settings = Button(text="Settings", background_normal='', background_color=BLACK)
        btn_settings.bind(on_press=self.open_settings)
        
        btn_home = Button(text="Home", background_normal='', background_color=BLACK)
        def go_home(instance):
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = 'home'
        btn_home.bind(on_press=go_home)
        
        btn_scan = Button(text="Scanner", background_normal='', background_color=BLACK)
        def go_scan(instance):
            self.manager.transition = SlideTransition(direction='down')
            self.manager.current = 'scanner'
        btn_scan.bind(on_press=go_scan)
        
        nav.add_widget(btn_settings)
        nav.add_widget(btn_home)
        nav.add_widget(btn_scan)
        layout.add_widget(nav)
        
        self.add_widget(layout)

    def open_settings(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        btn_email = Button(text="Send Inventory to Gmail", background_normal='', background_color=GREEN)
        content.add_widget(btn_email)
        popup = Popup(title="Settings", content=content, size_hint=(0.8, 0.3))
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

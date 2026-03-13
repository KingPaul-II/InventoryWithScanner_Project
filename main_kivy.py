from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.core.window import Window

import exporter
import scanner
import database

# Tablet sizing
Window.size = (400, 600)

class InventoryApp(App):
    def build(self):
        database.create_db()
        self.layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

        title = Label(text="Inventory Scanner (Kivy)", font_size='25sp', bold=True, size_hint=(1, 0.2))
        self.layout.add_widget(title)

        btn_scan = Button(text="1. Open Camera Scanner", font_size='20sp', background_color=(0.2, 0.6, 1, 1))
        btn_scan.bind(on_press=self.run_scanner)
        self.layout.add_widget(btn_scan)

        btn_excel = Button(text="2. Export to Excel", font_size='20sp', background_color=(0.1, 0.8, 0.1, 1))
        btn_excel.bind(on_press=self.run_excel_export)
        self.layout.add_widget(btn_excel)

        btn_text = Button(text="3. Export Text Summary", font_size='20sp', background_color=(0.8, 0.5, 0.2, 1))
        btn_text.bind(on_press=self.run_text_export)
        self.layout.add_widget(btn_text)

        return self.layout

    def run_scanner(self, instance):
        print("Launching scanner...")
        unknown_barcode = scanner.start_scanner()
        if unknown_barcode:
            self.show_manual_entry_popup(unknown_barcode)

    def run_excel_export(self, instance):
        exporter.export_to_excel()
        print("Excel Exported!")

    def run_text_export(self, instance):
        exporter.export_to_text()
        print("Text Exported!")

    def show_manual_entry_popup(self, barcode):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=f"Barcode: {barcode}\nNot found online. Enter name:"))
        
        name_input = TextInput(hint_text="e.g., Boy Bawang", multiline=False, font_size='20sp')
        content.add_widget(name_input)
        
        btn_save = Button(text="Save Item", size_hint=(1, 0.4), background_color=(0.1, 0.8, 0.1, 1))
        content.add_widget(btn_save)
        
        popup = Popup(title="New Item Detected!", content=content, size_hint=(0.85, 0.4))
        
        def save_and_close(instance):
            item_name = name_input.text
            if item_name:
                database.add_or_update_item(barcode, item_name, 1)
                print(f"Saved via UI: {item_name}")
            popup.dismiss()
            
        btn_save.bind(on_press=save_and_close)
        popup.open()

if __name__ == "__main__":
    InventoryApp().run()

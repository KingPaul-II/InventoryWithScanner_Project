from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

# Import your working project files
import exporter
import scanner
import database

# Set a tablet-like window size for testing on your laptop
Window.size = (400, 600)

class InventoryApp(App):
    def build(self):
        # 1. Ensure the database is ready when the app opens
        database.create_db()

        # 2. Create the main layout (Vertical stacking)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

        # 3. Add a Title Label
        title = Label(text="Inventory Scanner UI", font_size='30sp', bold=True, size_hint=(1, 0.2))
        layout.add_widget(title)

        # 4. Button: Start Scanning
        btn_scan = Button(text="1. Open Camera Scanner", font_size='20sp', background_color=(0.2, 0.6, 1, 1))
        # This tells the button to run your scanner file when clicked!
        btn_scan.bind(on_press=self.run_scanner)
        layout.add_widget(btn_scan)

        # 5. Button: Export Excel
        btn_excel = Button(text="2. Export to Excel", font_size='20sp', background_color=(0.1, 0.8, 0.1, 1))
        btn_excel.bind(on_press=self.run_excel_export)
        layout.add_widget(btn_excel)

        # 6. Button: Export Text Summary
        btn_text = Button(text="3. Export Text Summary", font_size='20sp', background_color=(0.8, 0.5, 0.2, 1))
        btn_text.bind(on_press=self.run_text_export)
        layout.add_widget(btn_text)

        return layout

    # --- Actions for the Buttons ---
    def run_scanner(self, instance):
        print("Launching scanner...")
        # The scanner runs, and we wait to see if it catches an unknown barcode
        unknown_barcode = scanner.start_scanner()
        
        # If it handed back a barcode, open the popup!
        if unknown_barcode:
            self.show_manual_entry_popup(unknown_barcode)

    def show_manual_entry_popup(self, barcode):
        # 1. Build the inside of the Pop-up
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Instructions
        content.add_widget(Label(text=f"Barcode: {barcode}\nNot found online. Enter name:"))
        
        # Text Box for typing (Touchscreen friendly!)
        name_input = TextInput(hint_text="e.g., Boy Bawang", multiline=False, font_size='20sp')
        content.add_widget(name_input)
        
        # Save Button
        btn_save = Button(text="Save Item", size_hint=(1, 0.4), background_color=(0.1, 0.8, 0.1, 1))
        content.add_widget(btn_save)
        
        # 2. Create the Pop-up window
        popup = Popup(title="New Item Detected!", content=content, size_hint=(0.85, 0.4))
        
        # 3. What happens when they click Save?
        def save_and_close(instance):
            item_name = name_input.text
            if item_name: # Make sure they didn't leave it blank
                database.add_or_update_item(barcode, item_name, 1)
                print(f"Saved via UI: {item_name}")
            popup.dismiss() # Close the popup
            
        btn_save.bind(on_press=save_and_close)
        
        # 4. Show it on screen!
        popup.open()

    def run_excel_export(self, instance):
        print("Exporting Excel...")
        exporter.export_to_excel()

    def run_text_export(self, instance):
        print("Exporting Text...")
        exporter.export_to_text()

if __name__ == "__main__":
    InventoryApp().run()

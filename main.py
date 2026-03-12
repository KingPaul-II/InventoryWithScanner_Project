from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window

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
        scanner.start_scanner()

    def run_excel_export(self, instance):
        print("Exporting Excel...")
        exporter.export_to_excel()

    def run_text_export(self, instance):
        print("Exporting Text...")
        exporter.export_to_text()

if __name__ == "__main__":
    InventoryApp().run()

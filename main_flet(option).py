import flet as ft
import exporter
import scanner
import database

def main(page: ft.Page):
    page.title = "DLSU Inventory Scanner"
    
    # Classic window sizing that works on all versions
    page.window_width = 400
    page.window_height = 650
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 30
    
    database.create_db()

    def run_scanner(e):
        print("Launching scanner...")
        unknown_barcode = scanner.start_scanner()
        if unknown_barcode:
            show_manual_entry(unknown_barcode)

    def run_excel_export(e):
        exporter.export_to_excel()
        # Classic Snackbar syntax
        page.snack_bar = ft.SnackBar(ft.Text("Excel Exported!"), bgcolor="green")
        page.snack_bar.open = True
        page.update()

    def run_text_export(e):
        exporter.export_to_text()
        # Classic Snackbar syntax
        page.snack_bar = ft.SnackBar(ft.Text("Text Summary Exported!"), bgcolor="blue")
        page.snack_bar.open = True
        page.update()

    def show_manual_entry(barcode):
        name_input = ft.TextField(label="Item Name", autofocus=True)
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"New Barcode: {barcode}"),
            content=name_input,
        )

        def save_and_close(e):
            if name_input.value:
                database.add_or_update_item(barcode, name_input.value, 1)
                print(f"Saved: {name_input.value}")
            
            dialog.open = False
            page.update()

        dialog.actions = [ft.TextButton("Save Item", on_click=save_and_close)]
        
        # --- THE FIX: Inject directly into the UI overlay ---
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    page.add(
        ft.Text("Inventory UI", size=32, weight="bold"),
        ft.Divider(height=20, color="transparent"),
        
        ft.FilledButton("1. Open Camera Scanner", on_click=run_scanner, width=300, height=60, icon="camera_alt"),
        ft.Divider(height=10, color="transparent"),
        
        ft.FilledButton("2. Export to Excel", on_click=run_excel_export, width=300, height=60, icon="download"),
        ft.Divider(height=10, color="transparent"),
        
        ft.FilledButton("3. Export Text Summary", on_click=run_text_export, width=300, height=60, icon="description")
    )

if __name__ == "__main__":
    ft.app(target=main)

import sqlite3
import pandas as pd

def export_to_excel(filename="Inventory_Report.xlsx"):
    """Reads the database and saves it as a formatted Excel file."""
    try:
        conn = sqlite3.connect('inventory.db')
        # This reads the table directly into a Python 'DataFrame'
        df = pd.read_sql_query("SELECT * FROM inventory", conn)
        conn.close()

        if df.empty:
            print("Database is empty. Nothing to export.")
            return

        # Exporting to Excel
        df.to_excel(filename, index=False)
        print(f"Success! Excel report saved as: {filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

def export_to_text(filename="Inventory_Summary.txt"):
    """Saves a simple text summary of the inventory."""
    conn = sqlite3.connect('inventory.db')
    df = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()

    # 'sep' makes it look like a clean table in Notepad
    df.to_csv(filename, sep='\t', index=False)
    print(f"Success! Text summary saved as: {filename}")

if __name__ == "__main__":
    # You can test it by running this file directly
    export_to_excel()
    export_to_text()

import sqlite3
import pandas as pd

def export_to_excel(filename="Inventory_Report.xlsx"):
    """Reads the database and saves it as an auto-formatted Excel file."""
    try:
        conn = sqlite3.connect('inventory.db')
        df = pd.read_sql_query("SELECT * FROM inventory", conn)
        conn.close()

        if df.empty:
            print("Database is empty. Nothing to export.")
            return
        
        # 1. Capitalize headers and remove underscores
        df.columns = [col.upper().replace('_', ' ') for col in df.columns]

        # 2. Use ExcelWriter to control column widths
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventory')
            
            # Auto-adjust columns width to fit the longest text
            worksheet = writer.sheets['Inventory']
            for idx, col in enumerate(df.columns):
                # Find the maximum length in the column (including header)
                series = df.iloc[:, idx].astype(str)
                max_len = max(series.map(len).max(), len(col)) + 2 # Add a little padding
                
                # Convert index (0, 1, 2) to letters (A, B, C)
                col_letter = chr(65 + idx)
                worksheet.column_dimensions[col_letter].width = max_len

        print(f"Success! Auto-sized Excel report saved as: {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")

def export_to_text(filename="Inventory_Summary.txt"):
    """Saves a clean text summary that auto-adjusts spacing based on the longest word."""
    import sqlite3
    import pandas as pd
    
    conn = sqlite3.connect('inventory.db')
    df = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()

    if df.empty:
        print("Database is empty. Nothing to export.")
        return

    # Capitalize headers
    df.columns = [col.upper().replace('_', ' ') for col in df.columns]

    # DYNAMIC MATH: Find the longest text in each column and add 4 spaces of padding
    w0 = max(len(str(df.columns[0])), df.iloc[:, 0].astype(str).map(len).max()) + 4
    w1 = max(len(str(df.columns[1])), df.iloc[:, 1].astype(str).map(len).max()) + 4
    w2 = max(len(str(df.columns[2])), df.iloc[:, 2].astype(str).map(len).max()) + 2

    with open(filename, 'w') as f:
        # Apply the exact calculated widths
        header = f"{df.columns[0]:<{w0}}{df.columns[1]:<{w1}}{df.columns[2]:<{w2}}"
        f.write(header + "\n")
        
        # Draw underline that matches the exact total width perfectly
        f.write("=" * (w0 + w1 + len(str(df.columns[2]))) + "\n") 
        
        for index, row in df.iterrows():
            line = f"{str(row.iloc[0]):<{w0}}{str(row.iloc[1]):<{w1}}{str(row.iloc[2]):<{w2}}"
            f.write(line + "\n")
            
    print(f"Success! Dynamic text summary saved as: {filename}")

if __name__ == "__main__":
    export_to_excel()
    export_to_text()

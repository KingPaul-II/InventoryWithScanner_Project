import sqlite3

def create_db():
    """Creates the database file and the inventory table."""
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # We use TEXT for barcode because some barcodes start with 0
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            barcode TEXT PRIMARY KEY,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database and table initialized!")

def add_or_update_item(barcode, name, qty_to_add):
    """Adds a new item or updates the quantity of an existing one."""
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Check if item exists
    cursor.execute("SELECT quantity FROM inventory WHERE barcode = ?", (barcode,))
    result = cursor.fetchone()
    
    if result:
        # Item exists, so we add to the current quantity
        new_qty = result[0] + qty_to_add
        cursor.execute("UPDATE inventory SET quantity = ? WHERE barcode = ?", (new_qty, barcode))
    else:
        # New item, insert it
        cursor.execute("INSERT INTO inventory (barcode, item_name, quantity) VALUES (?, ?, ?)", 
                       (barcode, name, qty_to_add))
    
    conn.commit()
    conn.close()

# Run this once to make sure the file is created when you start
if __name__ == "__main__":
    create_db()

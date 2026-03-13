import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import requests
import sqlite3
import database

def check_local_db(barcode):
    """Checks if the barcode is already in our local database."""
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT item_name FROM inventory WHERE barcode = ?", (barcode,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def lookup_barcode_online(barcode):
    """Checks the Open Food Facts API for the product name."""
    print(f"Searching internet for {barcode}...")
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        headers = {'User-Agent': 'DLSU_InventoryProject - Android - Version 1.0'}
        response = requests.get(url, headers=headers, timeout=5).json()
        
        if response.get("status") == 1:
            name = response["product"].get("product_name", "Unknown Item")
            print(f"Found Online: {name}")
            return name
    except Exception as e:
        print(f"Internet error: {e}")
    return None

def start_scanner():
    cap = cv2.VideoCapture(0)
    print("Scanner Active. (Press 'q' to quit)")

    cv2.namedWindow("Inventory Scanner", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Inventory Scanner", cv2.WND_PROP_TOPMOST, 1)

    while True:
        ret, frame = cap.read()
        if not ret: break

        barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.UPCA, ZBarSymbol.UPCE])
        
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            
            # --- THE NEW LOGIC FLOW ---
            
            # STEP 1: Check Local Memory First
            local_name = check_local_db(barcode_data)
            if local_name:
                print(f"Found locally! Adding +1 to {local_name}")
                database.add_or_update_item(barcode_data, local_name, 1)
                
                # Add a tiny delay so it doesn't scan 50 times in one second
                cv2.waitKey(1500) 
                continue # Skip the rest and wait for the next item
            
            # STEP 2: Not local? Check the Internet
            item_name = lookup_barcode_online(barcode_data)
            
            # STEP 3: Not online? Ask the user via the Kivy UI
            if not item_name:
                print(f"!!! Barcode {barcode_data} not found. Sending to UI...")
                cap.release()
                cv2.destroyAllWindows()
                return barcode_data 
            
            # STEP 4: Found online! Save it.
            database.add_or_update_item(barcode_data, item_name, 1)
            print(f"Saved: {item_name} (Qty: 1)")
            cv2.waitKey(1000)

        cv2.imshow("Inventory Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

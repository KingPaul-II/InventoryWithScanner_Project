import cv2
from pyzbar import pyzbar
import requests
import database

def lookup_barcode_online(barcode):
    """Checks the Open Food Facts API for the product name."""
    print(f"Searching internet for {barcode}...")
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        # We add a 'User-Agent' so the website knows who we are (standard practice)
        headers = {'User-Agent': 'DLSU_InventoryProject - Android - Version 1.0'}
        response = requests.get(url, headers=headers, timeout=5).json()
        
        if response.get("status") == 1:
            name = response["product"].get("product_name", "Unknown Item")
            print(f"Found: {name}")
            return name
    except Exception as e:
        print(f"Internet error: {e}")
    
    return None

def start_scanner():
    cap = cv2.VideoCapture(0)
    print("Scanner Active. (Press 'q' to quit)")

    while True:
        ret, frame = cap.read()
        if not ret: break

        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            
            # --- NEW LOGIC START ---
            # 1. Try to find the name online
            item_name = lookup_barcode_online(barcode_data)
            
            # 2. If not found online, ask the user in the terminal
            if not item_name:
                print(f"!!! Barcode {barcode_data} not found in database.")
                item_name = input("Please enter the name for this item: ")
            
            # 3. Save to your local database
            database.add_or_update_item(barcode_data, item_name, 1)
            print(f"Saved: {item_name} (Qty: 1)")
            # --- NEW LOGIC END ---

        cv2.imshow("Inventory Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    database.create_db()
    start_scanner()

import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import requests
import sqlite3
import database
from collections import Counter
import time # <-- NEW: Allows us to use a cooldown timer

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

    scan_buffer = [] 
    last_scan_time = 0       # <-- NEW: Memory of when we last scanned
    COOLDOWN_SECONDS = 3.0   # <-- NEW: How long to ignore the camera (3 seconds)

    while True:
        ret, frame = cap.read()
        if not ret: break

        current_time = time.time()

        # --- THE FIX: The Cooldown Shield ---
        # If 3 seconds haven't passed since the last scan, ignore everything
        if current_time - last_scan_time < COOLDOWN_SECONDS:
            time_left = int(COOLDOWN_SECONDS - (current_time - last_scan_time)) + 1
            cv2.putText(frame, f"Success! Pull item away... ({time_left}s)", 
                        (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Inventory Scanner", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                break
            continue # Skip the rest of the loop! Don't even look for barcodes.

        # --- Normal Scanning Logic ---
        barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.UPCA, ZBarSymbol.UPCE])
        
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            scan_buffer.append(barcode_data)
            break 
            
        if 0 < len(scan_buffer) < 5:
            cv2.putText(frame, f"Analyzing... Hold still! ({len(scan_buffer)}/5)", 
                        (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
        if len(scan_buffer) >= 5:
            winner_barcode = Counter(scan_buffer).most_common(1)[0][0]
            print(f"Consensus reached: {winner_barcode}")
            
            # STEP 1: Check Local Memory First
            local_name = check_local_db(winner_barcode)
            if local_name:
                print(f"Found locally! Adding +1 to {local_name}")
                database.add_or_update_item(winner_barcode, local_name, 1)
                scan_buffer.clear()
                last_scan_time = time.time() # <-- Trigger the cooldown!
                continue
            
            # STEP 2: Not local? Check the Internet
            item_name = lookup_barcode_online(winner_barcode)
            
            # STEP 3: Not online? Ask the user via the UI
            if not item_name:
                print(f"!!! Barcode {winner_barcode} not found. Sending to UI...")
                cap.release()
                cv2.destroyAllWindows()
                return winner_barcode 
            
            # STEP 4: Found online! Save it.
            database.add_or_update_item(winner_barcode, item_name, 1)
            print(f"Saved: {item_name} (Qty: 1)")
            scan_buffer.clear()
            last_scan_time = time.time() # <-- Trigger the cooldown!

        cv2.imshow("Inventory Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

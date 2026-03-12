import cv2
from pyzbar import pyzbar
import database  # This imports the file you made earlier!

def start_scanner():
    # 1. Initialize the camera
    cap = cv2.VideoCapture(0)
    print("Camera active. Point it at a barcode! (Press 'q' to stop)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 2. Find and decode barcodes in the frame
        barcodes = pyzbar.decode(frame)

        for barcode in barcodes:
            # Extract the barcode data as a string
            barcode_data = barcode.data.decode("utf-8")
            
            # Draw a rectangle around the barcode in the video feed
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            print(f"Scanned Barcode: {barcode_data}")

            # 3. Logic: If scanned, update the database
            # For now, we'll label everything "New Item" until we build the UI
            database.add_or_update_item(barcode_data, "New Item", 1)
            print(f"Updated {barcode_data} in database.")

        # Display the camera feed
        cv2.imshow("Inventory Scanner", frame)

        # Stop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Ensure the database table exists before scanning
    database.create_db()
    start_scanner()

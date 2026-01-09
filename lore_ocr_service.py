import os
import time
from pymongo import MongoClient
from PIL import Image
import pytesseract
from dotenv import load_dotenv

# --------------------
# Load environment variables
# --------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "pokemon_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "images")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 3))

# Lore crop box
LORE_CROP_BOX = tuple(map(int, os.getenv("LORE_CROP_BOX", "228,923,699,1016").split(",")))

# --------------------
# Connect to MongoDB
# --------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --------------------
# Optional: specify tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# --------------------

# --------------------
# Helper function
# --------------------
def process_image(doc):
    image_path = doc.get("filepath")
    if not image_path or not os.path.exists(image_path):
        print(f"[Error] File not found: {image_path}")
        return

    record_id = str(doc["_id"])

    print(f"[Found record] id: {record_id}, loading image: {image_path}")
    try:
        img = Image.open(image_path)
        cropped = img.crop(LORE_CROP_BOX)
        # Extract text
        text = pytesseract.image_to_string(cropped)
        text = text.strip()
        print(f"[Extracted text] {text}")
    except Exception as e:
        print(f"[Error] OCR failed: {e}")
        return

    # Update database
    try:
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"lore": text}}
        )
        print(f"[Updated data store] lore field updated")
    except Exception as e:
        print(f"[Error] Failed to update database: {e}")

# --------------------
# Main loop
# --------------------
def main():
    print("[Starting Lore OCR Service...]")
    while True:
        try:
            # Find unprocessed images
            unprocessed = collection.find({"lore": None})
            for doc in unprocessed:
                process_image(doc)
        except Exception as e:
            print(f"[Error] DB query failed: {e}")

        time.sleep(POLL_INTERVAL)
        print("[Checking for unprocessed images...]")

if __name__ == "__main__":
    main()

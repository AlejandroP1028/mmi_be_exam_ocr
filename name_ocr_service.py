import time
from pymongo import MongoClient
from bson import ObjectId
from PIL import Image
import pytesseract
import os
from dotenv import load_dotenv

# --------------------
# Load environment variables
# --------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017"  )
DB_NAME = os.getenv("DB_NAME", "pokemon_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "images")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 3))

# Convert crop box string to tuple of ints
NAME_CROP_BOX = tuple(map(int, os.getenv("NAME_CROP_BOX").split(",")))

# --------------------
# Connect to DB
# --------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --------------------
# Helper
# --------------------
def process_image(doc):
    image_path = doc.get("filepath")
    if not image_path or not os.path.exists(image_path):
        print(f"[Error] File not found: {image_path}")
        return

    print(f"[Found record] id: {doc['_id']}, loading image: {image_path}")
    try:
        img = Image.open(image_path)
        cropped = img.crop(NAME_CROP_BOX)
    except Exception as e:
        print(f"[Error] Failed to open/crop image: {e}")
        return

    try:
        name_text = pytesseract.image_to_string(cropped).strip()
        if not name_text:
            name_text = "UNKNOWN"
    except Exception as e:
        print(f"[Error] OCR failed: {e}")
        name_text = "UNKNOWN"

    # Update database
    try:
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"name": name_text}}
        )
        print(f"[Updated] name = '{name_text}'")
    except Exception as e:
        print(f"[Error] DB update failed: {e}")

# --------------------
# Main loop
# --------------------
def main():
    print("[Starting Name OCR Service...]")
    while True:
        try:
            unprocessed = collection.find({"name": None})
            for doc in unprocessed:
                process_image(doc)
        except Exception as e:
            print(f"[Error] DB query failed: {e}")

        time.sleep(POLL_INTERVAL)
        print("[Checking for unprocessed images...]")

if __name__ == "__main__":
    main()

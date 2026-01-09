import os
import time
from pymongo import MongoClient
from PIL import Image
from dotenv import load_dotenv

# --------------------
# Load environment variables
# --------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "pokemon_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "images")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 3))
WEAKNESS_DIR = os.getenv("WEAKNESS_DIR", "weaknesses")

# Weakness crop box (left, top, right, bottom)
WEAKNESS_CROP_BOX = (33, 882, 206, 911)

# --------------------
# Ensure directory exists
# --------------------
os.makedirs(WEAKNESS_DIR, exist_ok=True)

# --------------------
# Connect to MongoDB
# --------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --------------------
# Helper function
# --------------------
def process_image(doc):
    image_path = doc.get("filepath")
    if not image_path or not os.path.exists(image_path):
        print(f"[Error] File not found: {image_path}")
        return

    record_id = str(doc["_id"])
    output_path = os.path.join(WEAKNESS_DIR, f"{record_id}.png")

    print(f"[Found record] id: {record_id}, loading image: {image_path}")
    try:
        img = Image.open(image_path)
        cropped = img.crop(WEAKNESS_CROP_BOX)
        cropped.save(output_path)
        print(f"[Saved cropped image] {output_path}")
    except Exception as e:
        print(f"[Error] Failed to crop/save image: {e}")
        return

    # Update database
    try:
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"weakness_filepath": output_path}}
        )
        print(f"[Updated data store] weakness_filepath = {output_path}")
    except Exception as e:
        print(f"[Error] Failed to update database: {e}")

# --------------------
# Main loop
# --------------------
def main():
    print("[Starting Weakness OCR Service...]")
    while True:
        try:
            # Find unprocessed images
            unprocessed = collection.find({"weakness_filepath": None})
            for doc in unprocessed:
                process_image(doc)
        except Exception as e:
            print(f"[Error] DB query failed: {e}")

        time.sleep(POLL_INTERVAL)
        print("[Checking for unprocessed images...]")

if __name__ == "__main__":
    main()

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
MOVES_DIR = os.getenv("MOVES_DIR", "moves")

# Moves crop box (left, top, right, bottom)
MOVES_CROP_BOX = tuple(map(int, os.getenv("MOVES_CROP_BOX", "50,400,500,600").split(",")))

# --------------------
# Ensure directory exists
# --------------------
os.makedirs(MOVES_DIR, exist_ok=True)

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
    output_path = os.path.join(MOVES_DIR, f"{record_id}.png")

    print(f"[Found record] id: {record_id}, loading image: {image_path}")
    try:
        img = Image.open(image_path)
        cropped = img.crop(MOVES_CROP_BOX)
        cropped.save(output_path)
        print(f"[Saved cropped image] {output_path}")
    except Exception as e:
        print(f"[Error] Failed to crop/save image: {e}")
        return

    # Update database
    try:
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"moves_filepath": output_path}}
        )
        print(f"[Updated data store] moves_filepath = {output_path}")
    except Exception as e:
        print(f"[Error] Failed to update database: {e}")

# --------------------
# Main loop
# --------------------
def main():
    print("[Starting Moves OCR Service...]")
    while True:
        try:
            # Find unprocessed images
            unprocessed = collection.find({"moves_filepath": None})
            for doc in unprocessed:
                process_image(doc)
        except Exception as e:
            print(f"[Error] DB query failed: {e}")

        time.sleep(POLL_INTERVAL)
        print("[Checking for unprocessed images...]")

if __name__ == "__main__":
    main()

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
import os
import shutil
from dotenv import load_dotenv

# --------------------
# Configuration
# --------------------
load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploaded_images") 
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "pokemon_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "images")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --------------------
# App & DB
# --------------------
app = FastAPI()

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --------------------
# Helpers
# --------------------
def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# --------------------
# Routes
# --------------------
@app.post("/")
async def upload_image(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    filepath = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="File save failed")

    document = {
        "filename": file.filename,
        "filepath": filepath,
        "uploaded": True,
        "name": None,
        "lore": None,
        "weakness_filepath": None,
        "resistance_filepath": None,
        "moves_filepath": None,
    }

    try:
        result = collection.insert_one(document)
    except Exception:
        raise HTTPException(status_code=500, detail="Database insert failed")

    return JSONResponse(
        status_code=201,
        content={
            "id": str(result.inserted_id),
            "filename": file.filename,
            "message": "File uploaded and document created in MongoDB.",
        },
    )


@app.get("/{image_id}")
def get_image_metadata(image_id: str):
    try:
        doc = collection.find_one({"_id": ObjectId(image_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if not doc:
        raise HTTPException(status_code=404, detail="Record not found")

    return serialize_doc(doc)

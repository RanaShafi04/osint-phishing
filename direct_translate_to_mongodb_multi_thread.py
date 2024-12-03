import zlib  # For compression
import threading
from hashlib import sha256
from pymongo import MongoClient, errors
from translate_transformer import translate_text_to_french
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
TARGET_LANGUAGE = 'fr'
NUM_THREADS = 4  # Configurable number of threads
QUERY_LIMIT = 16  # Number of documents to process

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")  # Adjust URI accordingly
db = client['osint-phishing']
collection = db['dataset1-fr']

# Ensure the 'hash' field is unique
collection.create_index([('hash', 1)], unique=True)

def update_translate_to_mongo(document):
    try:
        email_text = document['email_text']
        email_bytes = email_text.encode('utf-8')

        # Define threshold for compression (e.g., 10 KB)
        threshold_size = 10240  # 10 KB

        # Compress large text
        if len(email_bytes) > threshold_size:
            compressed_email_text = zlib.compress(email_bytes)
            document['email_text'] = compressed_email_text
            document['is_compressed'] = True
        else:
            document['is_compressed'] = False

        # Calculate hash
        hash_value = sha256(email_bytes).hexdigest()
        document['hash'] = hash_value

        # Check if translation already exists
        query = {
            "hash": hash_value,
            TARGET_LANGUAGE: {"$exists": False}
        }

        # Fetch the document needing translation
        if collection.find_one(query):
            # Translate and compress if necessary
            translated_text = translate_text_to_french(email_text)
            if len(email_bytes) > threshold_size:
                translated_text = zlib.compress(translated_text.encode('utf-8'))

            # Update with translated text
            collection.update_one(
                {"_id": document["_id"]},
                {"$set": {TARGET_LANGUAGE: translated_text}}
            )
            print(f"Document updated: {document['_id']}")
        else:
            print("No document found needing translation.")
    except errors.DuplicateKeyError:
        print(f"Duplicate document: {document['_id']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    cursor = collection.find(
        {TARGET_LANGUAGE: {"$exists": False}}
    ).limit(QUERY_LIMIT)

    # Use ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(update_translate_to_mongo, doc) for doc in cursor]

        for future in as_completed(futures):
            future.result()  # Handle any exceptions

    print("Translation completed.")

import zlib  # For compression
import threading
from hashlib import sha256
from pymongo import MongoClient, errors
from translate_transformer import translate_text_to_french
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
TARGET_LANGUAGE = 'fr'
TRANSLATION_THRESHOLD_CHAR = 100_000  # Character limit for translation
NUM_THREADS = 4  # Configurable number of threads

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")  # Adjust URI accordingly
db = client['osint-phishing']
collection = db['dataset1-fr']

# Ensure the 'hash' field is unique
collection.create_index([('hash', 1)], unique=True)

# Lock for thread-safe operations on shared variables
lock = threading.Lock()
translated_char_count = 0  # Shared variable to track the total translated characters


def update_translate_to_mongo(document):
    global translated_char_count

    try:
        email_text = document['email_text']
        email_bytes = email_text.encode('utf-8')

        # Define threshold (e.g., 10 KB)
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
            "hash": str(hash_value),
            TARGET_LANGUAGE: {"$exists": False}
        }

        # Fetch the document that needs translation
        if collection.find_one(query):
            with lock:
                if translated_char_count + len(email_text) > TRANSLATION_THRESHOLD_CHAR:
                    return -1  # Stop execution signal

            # Translate and compress if necessary
            translated_text = translate_text_to_french(email_text)
            if len(email_bytes) > threshold_size:
                translated_text = zlib.compress(translated_text.encode('utf-8'))

            # Update with translated text
            collection.update_one(
                {"_id": document["_id"]},
                {"$set": {TARGET_LANGUAGE: translated_text}}
            )

            with lock:
                translated_char_count += len(email_text)
                print(f"Document updated: {TARGET_LANGUAGE}")
            return len(email_text)
        else:
            print("No document found needing translation.")
            return 0
    except errors.DuplicateKeyError:
        print(f"Duplicate document: {document['_id']}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 0


if __name__ == '__main__':
    cursor = collection.find({TARGET_LANGUAGE: {"$exists": False}})

    # Use ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(update_translate_to_mongo, doc) for doc in cursor]

        for future in as_completed(futures):
            result = future.result()
            if result == -1:  # Stop execution if threshold exceeded
                print("Translation limit reached. Exiting.")
                break

    # Log the total characters translated
    with open("translate_log.txt", "a") as f:
        log = f"Total translated characters: {translated_char_count} in language {TARGET_LANGUAGE}\n"
        print(log)
        f.write(log)

    print("Translation completed.")

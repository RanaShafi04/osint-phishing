from hashlib import sha256
from pymongo import MongoClient, errors
import zlib  # For compression
from translate_transformer import translate_text_to_french

TARGET_LANGUAGE = 'fr'
TRANSLATION_THRESHOLD_CHAR = 10_000  # Limit for translation

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")  # Adjust URI accordingly
db = client['osint-phishing']
collection = db['dataset1-fr']

# Ensure the 'hash' field is unique
collection.create_index([('hash', 1)], unique=True)


def update_translate_to_mongo(document, current_count):
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
            # Check character threshold limit
            next_count = current_count + len(email_text)
            if next_count > TRANSLATION_THRESHOLD_CHAR:
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
            print(f"Document updated with language: {TARGET_LANGUAGE}")
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
    count = 0
    cursor = collection.find({TARGET_LANGUAGE: {"$exists": False}})

    for document in cursor:
        next_count = update_translate_to_mongo(document, count)
        if next_count < 0:  # Stop execution when threshold is exceeded
            print("Translation limit reached. Exiting.")
            break
        count += next_count

    with open("translate_log.txt", "a") as f:
        log = f"Total translated characters: {count} in language {TARGET_LANGUAGE}\n"
        print(log)
        f.write(log)

    print("Translation completed.")

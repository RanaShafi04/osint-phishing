import zlib
from hashlib import sha256
from pymongo import MongoClient, errors
from translate_transformer import translate_text_to_target_lang
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Configuration
TARGET_LANGUAGE = 'ru'
NUM_THREADS = 6  # Configurable number of threads
QUERY_LIMIT = 10  # Number of documents to process
LOG_FILE = "translate.log"  # Log file name
FAIL_LOG_FILE = "fail_translation.log"  # Fail log file name

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client['osint-phishing']
collection = db['dataset1-fr']

collection.create_index([('hash', 1)], unique=True)

def log_error_to_file(error_message, document_hash):
    """Log errors with the document hash to a separate fail log file."""
    with open(FAIL_LOG_FILE, "a") as fail_log:
        fail_log.write(f"Translation Error with document {document_hash}: {error_message}\n")

def update_translate_to_mongo(document):
    try:
        email_text = document['email_text']
        # Handle error if email_text is not a string (e.g., already compressed)
        if isinstance(email_text, bytes):
            raise TypeError(
                f"'email_text' is of type 'bytes', cannot encode. Document hash: {document.get('hash', 'unknown')}")

        email_bytes = email_text.encode('utf-8')  # This should now work, as email_text is a string
        threshold_size = 10240  # 10 KB

        # Compress large text
        is_large = len(email_bytes) > threshold_size
        document['email_text'] = zlib.compress(email_bytes) if is_large else email_text
        document['is_compressed'] = is_large

        hash_value = sha256(email_bytes).hexdigest()
        document['hash'] = hash_value

        # Check if translation is needed
        if not collection.find_one({"hash": hash_value, TARGET_LANGUAGE: {"$exists": False}}):
            print(f"No translation needed for document: {document['_id']}")
            return

        # Translate and compress if necessary
        translated_text = translate_text_to_target_lang(email_text, TARGET_LANGUAGE)
        if is_large:
            translated_text = zlib.compress(translated_text.encode('utf-8'))

        # Update document in MongoDB
        collection.update_one(
            {"_id": document["_id"]},
            {"$set": {TARGET_LANGUAGE: translated_text}}
        )
        print(f"Document updated: {document['_id']}")
    except errors.DuplicateKeyError:
        print(f"Duplicate document: {document['_id']}")
    except Exception as e:
        print(f"Error: {e}")
        log_error_to_file(str(e), document.get('hash', 'unknown'))  # Log error to fail log

if __name__ == '__main__':
    start_time = datetime.now()  # Log start time
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"Translation started at: {start_time}\n")

    cursor = collection.find(
        {TARGET_LANGUAGE: {"$exists": False}}
    ).sort('_id', 1).limit(QUERY_LIMIT)

    # Use ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(update_translate_to_mongo, doc) for doc in cursor]

        for future in as_completed(futures):
            future.result()  # Handle any exceptions

    end_time = datetime.now()  # Log end time
    execution_time = end_time - start_time
    average_time_per_record = execution_time.total_seconds() / QUERY_LIMIT

    # Write log details to the file
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"Translation completed at: {end_time}\n")
        log_file.write(f"Total execution time: {execution_time}\n")
        log_file.write(f"Total translated record: {QUERY_LIMIT}\n")
        log_file.write(f"Number of threads: {NUM_THREADS}\n")
        log_file.write(f"Avg time per record in secconds: {average_time_per_record:.2f}\n")
        log_file.write("========================================\n")

    print("Translation completed.")
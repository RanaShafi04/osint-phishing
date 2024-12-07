from pymongo import MongoClient, errors
# from translate_transformer import translate_text_to_target_lang
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from utilities import collect_command_output

# Configuration
TARGET_KEY = 'nmap'
NUM_THREADS = 6  # Configurable number of threads
QUERY_LIMIT = 10  # Number of documents to process
LOG_FILE = f"{TARGET_KEY}.log"  # Log file name
FAIL_LOG_FILE = f"fail_{TARGET_KEY}.log"  # Fail log file name

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client['osint-phishing']
collection = db['dataset1-nmap']

collection.create_index([('hash', 1)], unique=True)

def log_error_to_file(error_message, document_hash):
    """Log errors with the document hash to a separate fail log file."""
    with open(FAIL_LOG_FILE, "a") as fail_log:
        fail_log.write(f"Translation Error with document {document_hash}: {error_message}\n")

def get_target_value(link):
    result = {}
    res = collect_command_output(f"nmap {link}", link, 'nmap', result)
    print(res)
    return result

def update_value_to_mongo(document):
    try:
        values = []
        for domain in document['domains']:
            value = get_target_value(domain)
            # Update document in MongoDB

        # save to Database
        # collection.update_one(
        #     {"_id": document["_id"]},
        #     {
        #         "$set": {
        #             TARGET_KEY: values,
        #         }
        #     }
        # )
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

    cursor = collection.find({
        '$and': [
            {'domains': {"$exists": True}},  # Check if 'domains' does not exist
            {'domains': {"$ne": []}}  # Ensure 'domains' is not an empty array
        ],
        # TARGET_KEY: {'$exists': False}  # Check if 'TARGET_KEY' does not exist
    }).sort('_id', 1).limit(QUERY_LIMIT)

    # Use ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(update_value_to_mongo, doc) for doc in cursor]

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
        log_file.write(f"Avg time per record in seconds: {average_time_per_record:.2f}\n")
        log_file.write("========================================\n")

    print(f"{TARGET_KEY} completed.")

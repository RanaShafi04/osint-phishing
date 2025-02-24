# -*- coding: utf-8 -*-
from pymongo import MongoClient, errors
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from process_utilities import parse_theharvester_output, merge_dictionaries

# Configuration
SRC_KEY = 'theharvester'
TARGET_KEY = 'theharvester_features'
NUM_THREADS = 6  # Number of threads for processing
QUERY_LIMIT = 50000  # Limit for documents to process
LOG_FILE = "theharvester_feature_processing.log"  # Log file name for success logs
FAIL_LOG_FILE = "fail_theharvester_feature_processing.log"  # Fail log file for error logs

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client['osint-phishing']
collection = db['dataset1-fr']

# Function to log errors into a separate file
def log_error_to_file(error_message, document_hash):
    """Log errors with the document hash to a separate fail log file."""
    with open(FAIL_LOG_FILE, "a") as fail_log:
        fail_log.write(f"Error with document {document_hash}: {error_message}\n")

# Function to process each document, run the theharvester scan and update MongoDB
def update_value_to_mongo(document):
    try:
        # Get existing features
        features = document[TARGET_KEY] if TARGET_KEY in document else {}

        for itm in document['theharvester']:
            features = merge_dictionaries(features,
                parse_theharvester_output(itm['output']))

        if features:
            # Update document in MongoDB
            collection.update_one(
                {"_id": document["_id"]},
                {"$set": {TARGET_KEY: features}}
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
        log_file.write(f"Script started at: {start_time}\n")

    # Query MongoDB to get the documents that need processing
    cursor = collection.find({
        '$and': [
            {SRC_KEY: {"$exists": True}},  # Check if SRC_KEY does not exist
            {SRC_KEY: {"$ne": []}}  # Ensure SRC_KEY is not an empty array
        ]
    }).sort('_id', 1).limit(QUERY_LIMIT)

    # Use ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(update_value_to_mongo, doc) for doc in cursor]

        for future in as_completed(futures):
            future.result()  # This will raise exceptions if any occur

    print("TheHarvester processing completed.")

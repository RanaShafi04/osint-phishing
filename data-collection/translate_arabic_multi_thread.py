# -*- coding: utf-8 -*-

# Note: run this command before executing this file for Google translate
# credentials variables.
# export GOOGLE_APPLICATION_CREDENTIALS="/Users/panharith/Documents/CyberMACS/Semester-1/Courses/Research-Method/Assignment/code/googleTranslate/keys/metal-incline-443410-k9-08dde4317b6e.json"

import subprocess
import zlib  # For compression
from pymongo import MongoClient, errors
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from utilities import google_translate_text

# Configuration
TARGET_KEY = 'ar'
RETRIES = 3
TIMEOUT = 120  # Increased timeout (2 minutes) to avoid Nmap timeout issues
NUM_THREADS = 6  # Number of threads for processing
QUERY_LIMIT = 10  # Limit for documents to process
LOG_FILE = "translate_arabic.log"  # Log file name for success logs
FAIL_LOG_FILE = "fail_translate_arabic.log"  # Fail log file for error logs

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client['osint-phishing']
collection = db['dataset1-fr']

# Run a command with retries and return the output
def run_command_with_retries(command, retries=RETRIES, timeout=TIMEOUT):
    try:
        # Use subprocess.Popen for real-time output handling
        print("running $ ", command)
        with subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        ) as process:
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode == 0:
                return stdout.strip()
            else:
                print(f"Command failed with error: {stderr.strip()}")
    except subprocess.TimeoutExpired:
        process.kill()
        print(f"Timeout expired for command: {command}")
    except Exception as e:
        print(f"Error executing command: {command} - {e}")
    return "Command failed after retries"

# Function to log errors into a separate file
def log_error_to_file(error_message, document_hash):
    """Log errors with the document hash to a separate fail log file."""
    with open(FAIL_LOG_FILE, "a") as fail_log:
        fail_log.write(f"Error with document {document_hash}: {error_message}\n")

# Function to process each document, run the Nmap scan and update MongoDB
def update_value_to_mongo(document):
    try:
        print(document['hash'])
        email_text = document['email_text']

        # Ensure it's a valid UTF-8 string
        if isinstance(email_text, bytes):
            email_text = email_text.decode('utf-8', errors='replace')

        translated_text = google_translate_text(TARGET_KEY, email_text)

        # Ensure translation output is UTF-8
        if isinstance(translated_text, bytes):
            translated_text = translated_text.decode('utf-8', errors='replace')

        email_bytes = email_text.encode('utf-8')

        # Define threshold (e.g., 10 KB)
        threshold_size = 10240  # 10 KB in bytes
        if len(email_bytes) > threshold_size:
            translated_text = zlib.compress(translated_text.encode('utf-8'))  # Compress safely

        new_value = {"$set": {TARGET_KEY: translated_text}}

        # Perform the update on the found document
        collection.update_one({"_id": document["_id"]}, new_value)
        print(f"Document updated with target language {TARGET_KEY}")

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
    # using aggregate() for random selection
    cursor = collection.aggregate([
        {'$match': {TARGET_KEY: {'$exists': False}}},  # Filter out documents where TARGET_KEY exists
        {'$sample': {'size': QUERY_LIMIT}}  # Randomly select QUERY_LIMIT documents
    ])
    # Use ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(update_value_to_mongo, doc) for doc in cursor]

        for future in as_completed(futures):
            future.result()  # This will raise exceptions if any occur

    end_time = datetime.now()  # Log end time
    execution_time = end_time - start_time
    average_time_per_record = execution_time.total_seconds() / QUERY_LIMIT

    # Write execution log details to the log file
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"Script completed at: {end_time}\n")
        log_file.write(f"Total execution time: {execution_time}\n")
        log_file.write(f"Total records processed: {QUERY_LIMIT}\n")
        log_file.write(f"Number of threads used: {NUM_THREADS}\n")
        log_file.write(f"Avg time per record: {average_time_per_record:.2f} seconds\n")
        log_file.write("========================================\n")

    print("Translated processing completed.")

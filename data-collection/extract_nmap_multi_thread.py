# -*- coding: utf-8 -*-
import subprocess
from pymongo import MongoClient, errors
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Configuration
TARGET_KEY = 'nmap'
RETRIES = 3
TIMEOUT = 120  # Increased timeout (2 minutes) to avoid Nmap timeout issues
NUM_THREADS = 6  # Number of threads for processing
QUERY_LIMIT = 180  # Limit for documents to process
LOG_FILE = "nmap.log"  # Log file name for success logs
FAIL_LOG_FILE = "fail_nmap.log"  # Fail log file for error logs

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
        values = []
        for domain in document['domains']:
            # Run Nmap scan for the domain
            cmd = f"nmap -Pn -T4 --max-retries {RETRIES} {domain}"
            nmap_output = run_command_with_retries(cmd)
            values.append({
                'datetime': datetime.now(),
                'domain': domain,
                'command': cmd,
                'output': nmap_output,
            })

        # Update document in MongoDB
        collection.update_one(
            {"_id": document["_id"]},
            {"$set": {"nmap": values}}
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
            {'domains': {"$exists": True}},  # Check if 'domains' does not exist
            {'domains': {"$ne": []}}  # Ensure 'domains' is not an empty array
        ],
        TARGET_KEY: {'$exists': False}  # Check if 'TARGET_KEY' does not exist
    }).sort('_id', 1).limit(QUERY_LIMIT)

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

    print("Nmap processing completed.")

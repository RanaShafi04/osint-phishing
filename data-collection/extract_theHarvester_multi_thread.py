# -*- coding: utf-8 -*-
import subprocess
import time
from pymongo import MongoClient, errors
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from utilities import extract_root_domain

# Configuration
TARGET_KEY = 'theharvester'
THE_HARVESTER_COMMAND = 'python theHarvester/theHarvester.py' # run via source code
# THE_HARVESTER_COMMAND = 'theHarvester' # run in Kali Linux
THEHARVESTER_ENGINE = 'all'

RETRIES = 3
DELAY_BETWEEN_RETRIES = 5  # Seconds
TIMEOUT = 120  # Increased timeout (2 minutes) to avoid timeout issues
NUM_THREADS = 6  # Number of threads for processing
QUERY_LIMIT = 100  # Limit for documents to process
LOG_FILE = "theharvester.log"  # Log file name for success logs
FAIL_LOG_FILE = "fail_theharvester.log"  # Fail log file for error logs

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

# # Function to process each document, run the theHarvester scan and update MongoDB
def run_theharvester(domain, command, retries=RETRIES, delay=DELAY_BETWEEN_RETRIES):
    """
    Run theHarvester command with retries and return the result if successful.

    Args:
        domain (str): The domain to scan.
        retries (int): Number of retry attempts.
        delay (int): Delay between retries in seconds.

    Returns:
        str: theHarvester output if successful.
        None: If all attempts fail.
    """
    for attempt in range(1, retries + 1):
        try:
            print(f"Running theHarvester for {domain}, Attempt {attempt}/{retries}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)

            # Check if theHarvester ran successfully
            if result.returncode == 0:
                print(f"theHarvester succeeded for {domain}")
                return result.stdout  # Return the output on success
            else:
                print(f"theHarvester failed for {domain} with error: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"Timeout expired for theHarvester: {command} (Attempt {attempt})")
        except Exception as e:
            print(f"Error executing theHarvester: {e} (Attempt {attempt})")

        # Delay before retrying
        if attempt < retries:
            time.sleep(delay)

    print(f"Failed to run theHarvester for {domain} after {retries} attempts.")
    return None  # Return None if all retries fail

def update_value_to_mongo(document):
    try:
        values = []
        for domain in document['domains']:
            root_domain = extract_root_domain(domain)
            if not root_domain:
                print(f"Fail to extract root domain from {domain}")
                continue
            # Run theHarvester scan for the domain
            command = f"{THE_HARVESTER_COMMAND} -d {root_domain} -l 500 -b {THEHARVESTER_ENGINE}"  # Customize as needed
            output = run_theharvester(domain, command)
            if output:
                print(output)
                values.append({
                    'datetime': datetime.now(),
                    'domain': domain,
                    'command': command,
                    'output': output,
                    'success': True,
                })

        # Update document in MongoDB
        collection.update_one(
            {"_id": document["_id"]},
            {"$set": {TARGET_KEY: values}}
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

    print("theHarvester processing completed.")

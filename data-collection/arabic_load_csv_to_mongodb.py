import pandas as pd
from hashlib import sha256
from pymongo import MongoClient, errors
import zlib  # For compression

FILE_PATH = '../dataset/arabic/arabic_dataset.csv'

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")  # Adjust your URI accordingly
db = client['osint-phishing']
collection = db['arabic']

# Create a unique index on the 'hash' field
collection.create_index([('hash', 1)], unique=True)

def loading_dataset():
    try:
        # Load dataset and replace NaN values with an empty string
        df = pd.read_csv(FILE_PATH,  sep = ';').fillna('')
        return df
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None

def insert_email_to_mongo(email_text, email_type):
    result = {}
    try:
        # Try to store uncompressed data for small emails
        email_bytes = email_text.encode('utf-8')

        # Define threshold (e.g., 10 KB)
        threshold_size = 10240  # 10 KB in bytes

        if len(email_bytes) > threshold_size:
            # Compress if larger than the threshold
            compressed_email_text = zlib.compress(email_bytes)
            result['email_text'] = compressed_email_text
            result['is_compressed'] = True  # Flag to indicate compression
        else:
            # Store uncompressed for smaller emails
            result['email_text'] = email_text
            result['is_compressed'] = False

        # Add other fields
        result['email_type'] = 'Phish Email' if email_type.startswith('Phish Email') else 'Legal Email'
        hash_value = sha256(email_bytes).hexdigest()
        result['hash'] = hash_value

        # Insert into MongoDB
        collection.insert_one(result)

    except errors.DuplicateKeyError:
        print(f"Document with hash {hash_value} already exists.")
    except Exception as e:
        print(f"An error occurred: {e}")


def iterate_each_row(df, start_index, end_index):
    # Ensure indices are within the DataFrame's range
    if start_index < 0 or end_index > len(df) or start_index >= end_index:
        print("Invalid index range specified.")
        return

    # Iterate over the specified range
    for index, row in df.iloc[start_index:end_index].iterrows():
        # Ensure essential fields are non-empty strings
        email_text = str(row['Email Text']).strip()
        email_type = str(row['Email Type']).strip()

        if not email_text or not email_type:
            continue  # Skip rows with missing values

        insert_email_to_mongo(email_text, email_type)

if __name__ == '__main__':
    print("Loading dataset")
    df = loading_dataset()
    if df is not None:
        start_index = 0# max(0, len(df) - 18000)  # Ensure the index is not negative
        end_index = len(df)  # End at the last row

        print(f"Iterating through each row. Start: {start_index}, End: {end_index}")
        iterate_each_row(df, start_index, end_index)

    print("Finished")

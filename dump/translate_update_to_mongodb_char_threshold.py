import pandas as pd
from hashlib import sha256
from pymongo import MongoClient, errors
import zlib  # For compression
from translate_transformer import translate_text_to_target_lang

FILE_PATH = '../dataset/official_Phishing_Email.csv'
TARGET_LANGUAGE = 'fr'
HAS_THRESHOLD_LIMIT = True
TRANSLATION_THRESHOLD_CHAR = 100_000

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")  # Adjust your URI accordingly
db = client['osint-phishing']
collection = db['dataset1-fr']

# Create a unique index on the 'hash' field
collection.create_index([('hash', 1)], unique=True)

def loading_dataset():
    try:
        # Load dataset and replace NaN values with an empty string
        df = pd.read_csv(FILE_PATH).fillna('')
        return df
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None

def update_translate_to_mongo(email_text, current_count):
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
        hash_value = sha256(email_bytes).hexdigest()
        result['hash'] = hash_value

        # Ensure the hash exists and TARGET_LANGUAGE is missing
        query = {
            "hash": str(hash_value),
            TARGET_LANGUAGE: {"$exists": False}
        }

        # Find the document with the specified hash that doesn't have TARGET_LANGUAGE
        document = collection.find_one(query)
        if document:

            # Validate on Threshold char
            next_count = current_count + len(document['email_text'])
            if HAS_THRESHOLD_LIMIT and next_count > TRANSLATION_THRESHOLD_CHAR:
                return -1 # signal to the caller function to stop the executiion

            # translated_text = translate_text(TARGET_LANGUAGE, document['email_text'])
            translated_text = translate_text_to_target_lang(document['email_text'])
            if len(email_bytes) > threshold_size:
                translated_text = zlib.compress(
                    bytes(translated_text, 'utf-8'))
            new_value = {
                "$set": {
                    TARGET_LANGUAGE: translated_text
                }
            }
            # Perform the update on the found document
            collection.update_one({"_id": document["_id"]}, new_value)
            print(f"Document updated with target language {TARGET_LANGUAGE}")
            return len(document['email_text'])
        else:
            print("No document found that needs updating.")
            return 0
    except errors.DuplicateKeyError:
        print(f"Document with hash {hash_value} already exists.")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

# def google_translate_text(target, text):
#     """Translates text into the target language.
#     Target must be an ISO 639-1 language code.
#     See https://g.co/cloud/translate/v2/translate-reference#supported_languages
#     """
#     return
#     import six
#     from google.cloud import translate_v2 as translate
#
#     translate_client = translate.Client()
#
#     if isinstance(text, six.binary_type):
#         text = text.decode("utf-8")
#
#     # Text can also be a sequence of strings, in which case this method
#     # will return a sequence of results for each text.
#     result = translate_client.translate(text, target_language=target)
#
#     # print(u"Text: {}".format(result["input"]))
#     # print(u"Translation: {}".format(result["translatedText"]))
#     # print(u"Detected source language: {}".format(result["detectedSourceLanguage"]))
#     return result["translatedText"]

def iterate_each_row(df, start_index, end_index):
    # Ensure indices are within the DataFrame's range
    if start_index < 0 or end_index > len(df) or start_index >= end_index:
        print("Invalid index range specified.")
        return

    count = 0
    # Iterate over the specified range
    for index, row in df.iloc[start_index:end_index].iterrows():
        # Ensure essential fields are non-empty strings
        email_text = str(row['Email Text']).strip()
        email_type = str(row['Email Type']).strip()

        if not email_text or not email_type:
            continue  # Skip rows with missing values

        next_count = update_translate_to_mongo(email_text, count)
        if next_count <0: # stop the execution when it's a negative count
            break
        count += next_count

    with open("../translate_log.txt", "a") as f:
        log = f"total translated characters = {count}. in language {TARGET_LANGUAGE}\n\n"
        print(log)
        f.write(log)

if __name__ == '__main__':
    # tr = google_translate_text('fr', 'Cambodia')
    # print(tr)
    print("Loading dataset")
    df = loading_dataset()
    if df is not None:
        start_index = 0# max(0, len(df) - 2000)  # Ensure the index is not negative
        end_index = len(df)  # End at the last row

        print(f"Iterating through each row. Start: {start_index}, End: {end_index}")
        iterate_each_row(df, start_index, end_index)

    print("Finished")

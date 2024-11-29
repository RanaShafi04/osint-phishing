# -*- coding: utf-8 -*-

import re
import subprocess
import pandas as pd
from mongodb_conn import mongo_collection, convert_objectid_to_str


FILE_PATH = './dataset/small_phishing_email.csv'
URL_PATTERN = r'\b(?:https?://|www\.)\S+\b'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

def loading_dataset():
    try:
        return pd.read_csv(FILE_PATH)
    except Exception as e:
        print(e)

def save_to_mongo():
    pass

def scrap_whois(websites):
    pass

def cleaning_dataset():
    pass
def extract_websites(email_text):
    print("--------")
    result = {
        'content': email_text,
        'whois': [],
        'dns': []
    }

    links = set(re.findall(URL_PATTERN, email_text))
    for link in links:
        # WHOIS lookup
        output = subprocess.getoutput(f"dig {link}")
        result['whois'].append({
            'link': link,
            'output': output
        })

    # emails = set(re.findall(EMAIL_PATTERN, email_text))
    # Convert result before writing

    result = convert_objectid_to_str(result)

    # Insert the dictionary into the collection
    insert_result = mongo_collection.insert_one(result)


def iterate_each_row(df):
    for index, row in df.head(20).iterrows():
        # print(row['EmailText'], row['EmailType'])
        extract_websites(row['EmailText'])

if __name__ == '__main__':
    df = loading_dataset()
    print(df.head())
    iterate_each_row(df)

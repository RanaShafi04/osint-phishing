# -*- coding: utf-8 -*-

import re
import subprocess
import pandas as pd
from mongodb_conn import mongo_collection, convert_objectid_to_str


FILE_PATH = './dataset/small_phishing_email.csv'
URL_PATTERN = r'\b(?:https?://|www\.)\S+\b'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
DOMAIN_EXTRACTION_PATTERN = r'^(?:https?:\/\/)?(?:www\.)?([^\/\n]+)'

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

def extract_domain(url):
    match = re.search(DOMAIN_EXTRACTION_PATTERN, url)
    if match:
        return match.group(1)
    return None

def extract_websites(email_text, email_type):
    result = {
        'content': email_text,
        'email_type': email_type,
        'whois': [],
        'dig': [],
        'nmap': [],
        'geolocation': [],
        'dns': [],
    }

    links = set(re.findall(URL_PATTERN, email_text))
    print(f"processing links {links}")
    for link in links:
        # WHOIS lookup
        output = subprocess.getoutput(f"dig {link}")
        result['dig'].append({
            'link': link,
            'output': output
        })

        domain = extract_domain(link)
        if domain:
            output = subprocess.getoutput(f"whois {domain}")
            result['whois'].append({
                'domain': domain,
                'output': output
            })
            # NMAP Geo location
            output = subprocess.getoutput(
                f"nmap --script ip-geolocation-geoplugin {domain}")
            result['geolocation'].append({
                'domain': domain,
                'output': output
            })
        
        # NMAP
        output = subprocess.getoutput(f"nmap {link}")
        result['nmap'].append({
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
        extract_websites(row['EmailText'], row['EmailType'])

if __name__ == '__main__':
    df = loading_dataset()
    print(df.head())
    iterate_each_row(df)

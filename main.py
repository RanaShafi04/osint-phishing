# -*- coding: utf-8 -*-

import re
import subprocess
import pandas as pd
from hashlib import sha256
from mongodb_conn import mongo_collection, convert_objectid_to_str


FILE_PATH = './dataset/small_phishing_email.csv'
URL_PATTERN = r'\b(?:https?://|www\.)\S+\b'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
DOMAIN_EXTRACTION_PATTERN = r'^(?:https?:\/\/)?(?:www\.)?([^\/\n]+)'

# Configuration
RETRIES = 3
TIMEOUT = 5  # seconds
THEHARVESTER_ENGINE = 'bing'

def loading_dataset():
    try:
        return pd.read_csv(FILE_PATH)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None

def run_command_with_retries(command, retries=RETRIES, timeout=TIMEOUT):
    for attempt in range(retries):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            print(f"Timeout expired for command: {command} (Attempt {attempt + 1} of {retries})")
        except Exception as e:
            print(f"Error executing command: {command} - {e}")
    return "Command failed after multiple attempts"

def extract_domain(url):
    match = re.search(DOMAIN_EXTRACTION_PATTERN, url)
    return match.group(1) if match else None

def collect_command_output(command, domain, command_type, result):
    output = run_command_with_retries(command)
    result[command_type].append({'domain': domain, 'output': output})

def extract_websites(email_text, email_type):
    result = {
        'hash': sha256(email_text.encode('utf-8')).hexdigest(),
        'content': email_text,
        'email_type': email_type,
        'links': [], # URLs
        'domains': [],
        'subdomains':[],
        'whois': [],
        'dig': [],
        'nmap': [],
        'geolocation': [],
    }

    links = set(re.findall(URL_PATTERN, email_text))
    print(f"Processing links: {links}")
    domains = set()
    for link in links:
        domain = extract_domain(link)
        domains.add(domain)
        collect_command_output(f"dig {link}", link, 'dig', result)
        collect_command_output(f"nmap {link}", link, 'nmap', result)

    # remove duplicate domains
    subdomains = set()
    for domain in domains:
        print(domain)
        collect_command_output(f"whois {domain}", domain, 'whois', result)
        collect_command_output(
            f"nmap --script ip-geolocation-geoplugin {domain}", domain, 'geolocation', result)
        # find sub-domains with theHarvester
        harvesterCmd = f"theHarvester -d {domain} -b {THEHARVESTER_ENGINE}"
        output = collect_command_output(harvesterCmd, domain, 'subdomains', result)
        result['subdomains'].append({
            'domain': domain,
            'output': str(output)
        })


    result['domains'] = list(domains)
    result['subdomains'] = list(subdomains)

    result['emails'] = list(set(re.findall(EMAIL_PATTERN, email_text)))
    result['links'] = list(links)
    result = convert_objectid_to_str(result)
    mongo_collection.insert_one(result)

def iterate_each_row(df):
    for index, row in df.head(20).iterrows():
        extract_websites(row['EmailText'], row['EmailType'])

if __name__ == '__main__':
    print("Loading dataset")
    df = loading_dataset()
    if df is not None:
        print(df.head())
        print("Iterate each row")
        iterate_each_row(df)
    print("Finished")

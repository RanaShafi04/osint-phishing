# -*- coding: utf-8 -*-

import re
from mongodb_conn import mongo_collection, convert_objectid_to_str

URL_PATTERN = r'\b(?:https?://|www\.)\S+\b'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
DOMAIN_EXTRACTION_PATTERN = r'^(?:https?:\/\/)?(?:www\.)?([^\/\n]+)'

# Configuration
RETRIES = 3
TIMEOUT = 5  # seconds

def extract_domain(url):
    match = re.search(DOMAIN_EXTRACTION_PATTERN, url)
    return match.group(1) if match else None

def extract_domain_link_email(email_text):
    result = {}

    links = set(re.findall(URL_PATTERN, email_text))
    result['domains'] = list(set([extract_domain(link) for link in links]))
    result['emails'] = list(set(re.findall(EMAIL_PATTERN, email_text)))
    result['links'] = list(links)
    result = convert_objectid_to_str(result)
    return result

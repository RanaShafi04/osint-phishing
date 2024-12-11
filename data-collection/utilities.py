# -*- coding: utf-8 -*-

import re
import subprocess
from mongodb_conn import convert_objectid_to_str

URL_PATTERN = r'\b(?:https?://|www\.)\S+\b'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
ROOT_DOMAIN_PATTERN = r"([a-zA-Z0-9-]+\.[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})?)$"

# DOMAIN_EXTRACTION_PATTERN = r'^(?:https?:\/\/)?(?:www\.)?([^\/\n]+)'
DOMAIN_EXTRACTION_PATTERN = r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"

# Configuration
RETRIES = 3
TIMEOUT = 5  # seconds

# Generic TLDs (gTLDs)
GENERIC_TLDS = [
    ".com", ".org", ".net", ".info", ".biz", ".name", ".pro", ".coop", ".aero", ".museum", ".int",
    ".edu", ".gov", ".mil", ".jobs", ".mobi", ".travel", ".tel", ".post", ".asia", ".cat", ".xxx",
    ".club", ".online", ".site", ".store", ".tech", ".app", ".blog", ".shop", ".cloud", ".dev",
    ".art", ".company", ".design", ".group", ".software", ".agency", ".media", ".network"
]

# Country-code TLDs (ccTLDs)
COUNTRY_TLDS = [
    ".ac", ".ad", ".ae", ".af", ".ag", ".ai", ".al", ".am", ".ao", ".aq", ".ar", ".as", ".at", ".au", ".aw",
    ".ax", ".az", ".ba", ".bb", ".bd", ".be", ".bf", ".bg", ".bh", ".bi", ".bj", ".bm", ".bn", ".bo", ".bq",
    ".br", ".bs", ".bt", ".bv", ".bw", ".by", ".bz", ".ca", ".cc", ".cd", ".cf", ".cg", ".ch", ".ci", ".ck",
    ".cl", ".cm", ".cn", ".co", ".cr", ".cu", ".cv", ".cw", ".cx", ".cy", ".cz", ".de", ".dj", ".dk", ".dm",
    ".do", ".dz", ".ec", ".ee", ".eg", ".eh", ".er", ".es", ".et", ".eu", ".fi", ".fj", ".fk", ".fm", ".fo",
    ".fr", ".ga", ".gb", ".gd", ".ge", ".gf", ".gg", ".gh", ".gi", ".gl", ".gm", ".gn", ".gp", ".gq", ".gr",
    ".gs", ".gt", ".gu", ".gw", ".gy", ".hk", ".hm", ".hn", ".hr", ".ht", ".hu", ".id", ".ie", ".il", ".im",
    ".in", ".io", ".iq", ".ir", ".is", ".it", ".je", ".jm", ".jo", ".jp", ".ke", ".kg", ".kh", ".ki", ".km",
    ".kn", ".kp", ".kr", ".kw", ".ky", ".kz", ".la", ".lb", ".lc", ".li", ".lk", ".lr", ".ls", ".lt", ".lu",
    ".lv", ".ly", ".ma", ".mc", ".md", ".me", ".mg", ".mh", ".mk", ".ml", ".mm", ".mn", ".mo", ".mp", ".mq",
    ".mr", ".ms", ".mt", ".mu", ".mv", ".mw", ".mx", ".my", ".mz", ".na", ".nc", ".ne", ".nf", ".ng", ".ni",
    ".nl", ".no", ".np", ".nr", ".nu", ".nz", ".om", ".pa", ".pe", ".pf", ".pg", ".ph", ".pk", ".pl", ".pm",
    ".pn", ".pr", ".ps", ".pt", ".pw", ".py", ".qa", ".re", ".ro", ".rs", ".ru", ".rw", ".sa", ".sb", ".sc",
    ".sd", ".se", ".sg", ".sh", ".si", ".sj", ".sk", ".sl", ".sm", ".sn", ".so", ".sr", ".ss", ".st", ".sv",
    ".sx", ".sy", ".sz", ".tc", ".td", ".tf", ".tg", ".th", ".tj", ".tk", ".tl", ".tm", ".tn", ".to", ".tr",
    ".tt", ".tv", ".tw", ".tz", ".ua", ".ug", ".uk", ".us", ".uy", ".uz", ".va", ".vc", ".ve", ".vg", ".vi",
    ".vn", ".vu", ".wf", ".ws", ".ye", ".yt", ".za", ".zm", ".zw"
]

# Combine into one list
VALID_TLDS = GENERIC_TLDS + COUNTRY_TLDS

def is_valid_domain(domain):
    """Validate domain ends with a valid TLD."""
    return any(domain.endswith(tld) for tld in VALID_TLDS)

def extract_domain(url):
    """Extract and clean domain from a URL."""
    # Regular expression to extract domain
    match = re.search(DOMAIN_EXTRACTION_PATTERN, url)
    if match:
        domain = match.group(1)
        # Remove trailing invalid characters
        domain = domain.strip(")").strip(",:\"")
        # Validate domain
        return domain if is_valid_domain(domain) else None
    return None

def extract_domain_link_email(email_text):
    result = {}

    links = set(re.findall(URL_PATTERN, email_text))
    result['domains'] = list(set([extract_domain(link) for link in links]))
    result['emails'] = list(set(re.findall(EMAIL_PATTERN, email_text)))
    result['links'] = list(links)
    result = convert_objectid_to_str(result)
    return result

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

def collect_command_output(command, domain, command_type, result):
    output = run_command_with_retries(command)
    result[command_type].append({'domain': domain, 'output': output})

def extract_root_domain(domain_or_url):
    """
    Extracts the root domain from a given URL or domain string.

    Args:
        domain_or_url (str): The input URL or domain.

    Returns:
        str: The extracted root domain or None if not valid.
    """
    try:
        # Ensure input is a string
        if not isinstance(domain_or_url, str) or not domain_or_url.strip():
            return None

        # Match the root domain pattern
        match = re.search(ROOT_DOMAIN_PATTERN, domain_or_url.strip())
        if match:
            root_domain = match.group(1).lower()  # Convert to lowercase for consistency
            return f"{root_domain}" if is_valid_domain(root_domain) else None
    except Exception as e:
        print(f"Error extracting root domain: {e}")
    return None

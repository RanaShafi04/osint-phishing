import re

def parse_nmap_output(nmap_output):
    """
    Extracts features from the Nmap command output.
    Args:
        nmap_output (str): Raw Nmap command output as a string.
    Returns:
        dict: Extracted features in a structured dictionary.
    """
    features = {}

    # Extract IP Address
    ip_match = re.search(r'Nmap scan report for [^\s]+\s\(([\d.]+)\)', nmap_output)
    features['ip_address'] = ip_match.group(1) if ip_match else None

    # Extract Hostname
    hostname_match = re.search(r'Nmap scan report for ([^\s]+)', nmap_output)
    features['hostname'] = hostname_match.group(1) if hostname_match else None

    # Extract Host Up Status and Latency
    host_up_match = re.search(r'Host is up \(([\d.]+)s latency\)', nmap_output)
    features['host_up'] = 1 if host_up_match else 0
    features['latency'] = float(host_up_match.group(1)) if host_up_match else None

    # Extract Reverse DNS Record
    rdns_match = re.search(r'rDNS record for [\d.]+:\s([^\n]+)', nmap_output)
    features['rdns_record'] = rdns_match.group(1) if rdns_match else None

    # Extract Open Ports, Services, and Closed Ports
    open_ports = []
    services = []
    for match in re.finditer(r'(\d+)/tcp\s+(open|closed|filtered)\s+([^\s]+)', nmap_output):
        port, state, service = match.groups()
        if state == 'open':
            open_ports.append(int(port))
            services.append(service)

    features['open_ports_count'] = len(open_ports)
    features['open_ports'] = open_ports
    features['services'] = services

    # Extract Closed Ports
    closed_ports_match = re.search(r'Not shown: (\d+) filtered tcp ports', nmap_output)
    features['filtered_ports_count'] = int(closed_ports_match.group(1)) if closed_ports_match else 0

    # Extract Scan Duration
    duration_match = re.search(r'Nmap done: .+ scanned in ([\d.]+) seconds', nmap_output)
    features['scan_duration'] = float(duration_match.group(1)) if duration_match else None

    # Extract Alternate IP Addresses
    alt_ips_match = re.search(r'Other addresses for [^\s]+ \(not scanned\): ([\d., ]+)', nmap_output)
    if alt_ips_match:
        alt_ips = [ip.strip() for ip in alt_ips_match.group(1).split()]
        features['alternate_ip_count'] = len(alt_ips)
    else:
        features['alternate_ip_count'] = 0

    # Determine Common Web Ports and HTTPS Support
    common_web_ports = {80, 443}
    features['common_web_ports_open'] = 1 if any(port in open_ports for port in common_web_ports) else 0
    features['https_supported'] = 1 if 443 in open_ports else 0

    return features

def merge_dictionaries(dict1, dict2):
    """
    Merges two dictionaries where all values are lists or strings.
    Appends unique values of the same keys from both dictionaries as comma-separated strings.
    Handles non-iterable values (e.g., float, None) by treating them as empty strings.

    Args:
        dict1 (dict): The first dictionary.
        dict2 (dict): The second dictionary.

    Returns:
        dict: A merged dictionary with unique, comma-separated string values for matching keys.
    """
    merged_dict = {}

    # Get all unique keys from both dictionaries
    all_keys = set(dict1.keys()).union(dict2.keys())

    for key in all_keys:
        value1 = dict1.get(key, [])
        value2 = dict2.get(key, [])

        # Ensure values are treated as lists; handle non-iterable types
        if not isinstance(value1, list):
            value1 = [str(value1)] if value1 is not None else []
        if not isinstance(value2, list):
            value2 = [str(value2)] if value2 is not None else []

        # Combine values, deduplicate, and sort for consistency
        combined_values = set(map(str, value1 + value2))  # Convert all values to strings to handle mixed types

        # Convert the set to a sorted, comma-separated string
        merged_dict[key] = ", ".join(combined_values)
    return merged_dict

def extract_features_from_theharvester(output):
    """
    Extracts features from theHarvester command output.

    Args:
        output (str): Raw text output from theHarvester command.

    Returns:
        dict: Dictionary containing extracted features.
    """
    features = {}

    try:
        # Extract target domain
        target_match = re.search(r"\[\*\] Target: ([\w.-]+)", output)
        features['target_domain'] = target_match.group(1) if target_match else None

        # Extract emails
        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", output)
        features['emails'] = list(set(emails))  # Remove duplicates
        features['num_emails'] = len(features['emails'])

        # Extract hosts
        hosts_section = re.search(r"\[\*\] Hosts found:\s*\d+\s*[-]+\s*(.*?)(?=\[\*|\Z)", output, re.S)
        if hosts_section:
            hosts = re.findall(r"[\w.-]+\.[\w.-]+", hosts_section.group(1))
            features['hosts'] = list(set(hosts))  # Remove duplicates
            features['num_hosts'] = len(features['hosts'])
        else:
            features['hosts'] = []
            features['num_hosts'] = 0

        # Extract IP addresses
        ip_count = re.search(r"No IPs found\.|IPs found: (\d+)", output)
        features['num_ips'] = int(ip_count.group(1)) if ip_count and ip_count.group(1) else 0

        # Extract search sources
        search_sources = re.findall(r"[*] Searching (\w+)", output)
        features['search_sources'] = list(set(search_sources))

        # Capture any errors
        if "No IPs found" in output:
            features['errors'] = "No IPs found"

    except Exception as e:
        print(f"Error parsing theHarvester output: {e}")

    return features

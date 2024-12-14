from datetime import datetime

from pymongo import MongoClient, errors
import csv

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client['osint-phishing']
collection = db['dataset1-fr']

# Define fields to extract
nmap_keys = [
            "hostname", "scan_duration", "host_up", "alternate_ip_count",
            "ip_address", "common_web_ports_open", "open_ports_count",
            "latency", "filtered_ports_count", "open_ports", "rdns_record",
            "https_supported", "services"
        ]
theharvester_keys = ["host_found", "interesting_url", "asn_found", "ip_found"]
columns = ["email_text"] + nmap_keys + theharvester_keys + ["email_type"]

# Prepare CSV file
output_file = f"exported_data{datetime.now()}.csv"
with open(output_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()

    # Query all documents in the collection
    for document in collection.find():
        row = {}
        row["email_text"] = document.get("email_text", "")
        row["email_type"] = document.get("email_type", "")

        # Extract keys from nmap_features
        nmap_features = document.get("nmap_features", {})
        for key in nmap_keys:
            row[key] = nmap_features.get(key, "")

        # Extract keys from theharvester_features
        theharvester_features = document.get("theharvester_features", {})
        for key in theharvester_keys:
            row[key] = theharvester_features.get(key, "")

        # Write row to CSV
        writer.writerow(row)

print(f"Data exported to {output_file}")

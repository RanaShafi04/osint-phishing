import re
import subprocess
from bson import ObjectId
from pymongo import MongoClient

# Function to convert ObjectId to string recursively
def convert_objectid_to_str(data):
    if isinstance(data, dict):
        return {k: convert_objectid_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    return data

# Connect to the MongoDB server (default port 27017)
# Replace with your actual credentials
username = "admin"
password = "admin"
host = "localhost"  # or the hostname/IP of your MongoDB server
port = 27017        # default MongoDB port

# Create the connection string with authentication
uri = f"mongodb://{username}:{password}@{host}:{port}/"

# Establish the connection
client = MongoClient(uri)

# Access the database (replace 'my_database' with your actual database name)
db = client["osint-phishing"]
# Access or create a collection
collection = db["dataset1"]

content1 = """Hi,
Does anyone use partitioning on a Linux server? What is the recommended solution? UML? 
Cheers,
Sorin-- 
Irish Linux Users' Group: ilug@linux.ie
https://www.linux.ie/mailman/listinfo/ilug
http://www.linux.ie/mailman/listinfo/ilug for (un)subscription information.
List maintainer: listmaster@linux.ie
www.github.com
"""
url_pattern = r'\b(?:https?://|www\.)\S+\b'
email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

links = re.findall(url_pattern, content1)
print(links)
emails = re.findall(email_pattern, content1)

result = {
    'content': content1,
    'whois': [],
    'dns': []
}
for link in links:
    # WHOIS lookup
    output = subprocess.getoutput(f"dig {link}")
    result['whois'].append({
        'link': link,
        'output': output
    })

# Convert result before writing

result = convert_objectid_to_str(result)

# Insert the dictionary into the collection
insert_result = collection.insert_one(result)
# Print the ID of the inserted document
# print("Inserted document ID:", result.inserted_id)

# print(result)
# with open("result.json", "w") as outfile:
#     json.dump(result, outfile)


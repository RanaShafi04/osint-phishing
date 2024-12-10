# -*- coding: utf-8 -*-

from pymongo import MongoClient
from bson import ObjectId

# Connect to the MongoDB server (default port 27017)
# Replace with your actual credentials
USERNAME = "admin"
PASSWORD = "admin"
HOST = "localhost"  # or the hostname/IP of your MongoDB server
PORT = 27017        # default MongoDB port
DATABASE_NAME = "osint-phishing"
COLLECTION_NAME = "dataset1"

# Create the connection string with authentication
URI = f"mongodb://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/"
# Establish the connection
client = MongoClient(URI)

# Access the database (replace 'my_database' with your actual database name)
db = client[DATABASE_NAME]
# Access or create a collection
mongo_collection = db[COLLECTION_NAME]

# Function to convert ObjectId to string recursively
def convert_objectid_to_str(data):
    if isinstance(data, dict):
        return {k: convert_objectid_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    return data
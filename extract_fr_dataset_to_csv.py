import zlib
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from pathlib import Path

# Connect to MongoDB
client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client['osint-phishing']
collection = db['dataset1-fr']

# Load data from collection
cursor = collection.find({}, {'_id': 0})  # Exclude '_id' if not needed

# Function to decompress and decode fields
def decompress_field(field):
    try:
        if isinstance(field, bytes):
            return zlib.decompress(field).decode('utf-8')
        return field  # If not compressed, return as is
    except Exception as e:
        print(f"Decompression error: {e}")
        return None  # Handle decompression errors gracefully

# Process each document to decompress fields
data = []
for doc in cursor:
    # Decompress 'email_text' and 'fr' if they are compressed
    doc['email_text'] = decompress_field(doc.get('email_text'))
    doc['fr'] = decompress_field(doc.get('fr'))  # Assuming 'fr' might be compressed too
    data.append(doc)

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(data)

# Reorder columns as specified
desired_order = ['email_text', 'fr', 'hash', 'email_type']
df = df[desired_order]

# Ensure the output directory exists
output_dir = Path("dataset/fr")
output_dir.mkdir(parents=True, exist_ok=True)

# Save DataFrame to CSV
output_file = output_dir / f"dataset1-fr-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
df.to_csv(output_file, index=False)  # Save without DataFrame index

print(f"Data exported to {output_file}")
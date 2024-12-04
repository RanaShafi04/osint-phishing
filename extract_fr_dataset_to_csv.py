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

# Convert the cursor to a list of dictionaries
data = list(cursor)

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(data)

# Reorder columns
column_order = ['email_text', 'fr', 'email_type']  # Desired order
df = df[column_order]  # Reorder the DataFrame

# Display the DataFrame
print(df.tail())
print("Exporting to CSV file...")

# Ensure the directory exists
output_dir = Path("dataset/fr")
output_dir.mkdir(parents=True, exist_ok=True)

# Save DataFrame to CSV
output_file = output_dir / f"dataset1-fr-{datetime.now()}.csv"
df.to_csv(output_file, index=False)  # Save without DataFrame index

print(f"Data exported to {output_file}")

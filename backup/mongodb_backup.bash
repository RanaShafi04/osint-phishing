#!/bin/bash

# backup MongoDB collection and save it into zip files
HOST="127.0.0.1"
PORT=27017
USERNAME="admin"
PASSWORD="admin"
DATABASE="osint-phishing"
AUTH_DATABASE="admin"
COLLECTION="dataset1-fr"
OUTPUT_FILE="backup"-$(date +"%Y-%m-%d_%H-%M-%S")

backup() {
  # use mongodump command to create a new backup
  mongodump --host $HOST --port $PORT -u $USERNAME -p $PASSWORD \
  --db $DATABASE --collection $COLLECTION \
  --authenticationDatabase admin --out $OUTPUT_FILE
}

echo "Backup Starting"
backup
#create a zip file from the out folder
zip $OUTPUT_FILE.zip $OUTPUT_FILE
# delete the output folder, we need only the zip file
rm -rf $OUTPUT_FILE
echo "Backup Completed"

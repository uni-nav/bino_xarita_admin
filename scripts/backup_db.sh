#!/bin/bash

# Database Backup Script
# Usage: ./backup_db.sh [output_file]

set -e

# Load environment variables
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '#' | awk '/=/ {print $1}')
fi

DB_CONTAINER="bino_xarita_admin-db-1"  # Adjust container name if needed
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE=${1:-"backup_${TIMESTAMP}.sql"}
BACKUP_DIR="backups"

mkdir -p $BACKUP_DIR

echo "Starting backup for database: ${DB_NAME:-university_nav}..."

# Check if running in Docker
if command -v docker &> /dev/null && docker ps | grep -q $DB_CONTAINER; then
    docker exec -t $DB_CONTAINER pg_dump -U ${DB_USER:-postgres} ${DB_NAME:-university_nav} > "$BACKUP_DIR/$OUTPUT_FILE"
else
    # Local backup
    pg_dump -U ${DB_USER:-postgres} -h ${DB_HOST:-localhost} ${DB_NAME:-university_nav} > "$BACKUP_DIR/$OUTPUT_FILE"
fi

if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_DIR/$OUTPUT_FILE"
    # Compression
    gzip "$BACKUP_DIR/$OUTPUT_FILE"
    echo "Compressed to: $BACKUP_DIR/$OUTPUT_FILE.gz"
else
    echo "Backup failed!"
    exit 1
fi

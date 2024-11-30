#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups"

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U thingdata thingdata > "$BACKUP_DIR/db_$TIMESTAMP.sql"

# Compress backup
gzip "$BACKUP_DIR/db_$TIMESTAMP.sql"

echo "Backup completed: $BACKUP_DIR/db_$TIMESTAMP.sql.gz"
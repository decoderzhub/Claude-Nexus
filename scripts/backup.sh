#!/bin/bash
# Backup script for Claude Nexus data
# Backs up the data directory to a specified location (e.g., NAS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data"

# Default backup location - override with environment variable
BACKUP_DEST="${NEXUS_BACKUP_PATH:-$PROJECT_DIR/backups}"

# Create timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="nexus_backup_$TIMESTAMP"

echo "=================================="
echo "Claude Nexus Backup"
echo "=================================="
echo ""
echo "Source: $DATA_DIR"
echo "Destination: $BACKUP_DEST/$BACKUP_NAME"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DEST"

# Create backup
if command -v rsync &> /dev/null; then
    # Use rsync if available (better for large files)
    rsync -av --progress "$DATA_DIR/" "$BACKUP_DEST/$BACKUP_NAME/"
else
    # Fall back to tar
    tar -czvf "$BACKUP_DEST/$BACKUP_NAME.tar.gz" -C "$PROJECT_DIR" data
fi

echo ""
echo "Backup complete!"
echo ""

# Clean up old backups (keep last 10)
echo "Cleaning up old backups..."
cd "$BACKUP_DEST"
ls -t | tail -n +11 | xargs -r rm -rf

echo "Done."

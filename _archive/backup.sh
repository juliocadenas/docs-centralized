#!/bin/bash
# AI Hub Madrid - Backup Script
# Run via cron weekly: 0 3 * * 0 /mnt/seagate/scripts/backup.sh
# Creates tar.gz of all config/service files (NOT the models - too big)

BACKUP_DIR="/mnt/seagate/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ai_hub_backup_$DATE.tar.gz"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "Starting AI Hub backup..."

# Collect all config/service files
TEMP_DIR="/tmp/ai_hub_backup_$DATE"
mkdir -p "$TEMP_DIR"

# 1. Gateway code
cp -r /mnt/seagate/ai-hub-gateway "$TEMP_DIR/gateway" 2>/dev/null

# 2. AI Hub Studio code
cp -r /mnt/seagate/ai-hub-studio "$TEMP_DIR/studio" 2>/dev/null

# 3. Systemd service files
mkdir -p "$TEMP_DIR/systemd"
cp /etc/systemd/system/{ai-hub-gateway,tts,stt,musetalk,comfyui,wan2gp}.* "$TEMP_DIR/systemd/" 2>/dev/null
cp /etc/systemd/system/ollama.* "$TEMP_DIR/systemd/" 2>/dev/null

# 4. Docker configs
cp /mnt/seagate/*/docker-compose.yml "$TEMP_DIR/" 2>/dev/null
cp /mnt/seagate/*/Dockerfile "$TEMP_DIR/" 2>/dev/null

# 5. Model registry
cp /mnt/seagate/api/model_registry.yaml "$TEMP_DIR/" 2>/dev/null

# 6. Nginx/cron configs
cp /etc/nginx/sites-enabled/* "$TEMP_DIR/" 2>/dev/null
crontab -l > "$TEMP_DIR/crontab.txt" 2>/dev/null

# 7. Health check and scripts
cp /mnt/seagate/scripts/*.sh "$TEMP_DIR/" 2>/dev/null

# 8. Service wrapper apps (musetalk, liveportrait, etc)
cp /mnt/seagate/*/app.py "$TEMP_DIR/" 2>/dev/null
cp /mnt/seagate/*_app.py "$TEMP_DIR/" 2>/dev/null

# Create tarball
tar -czf "$BACKUP_FILE" -C /tmp "ai_hub_backup_$DATE"
rm -rf "$TEMP_DIR"

SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
echo "Backup created: $BACKUP_FILE ($SIZE)"

# Clean old backups
find "$BACKUP_DIR" -name "ai_hub_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null
echo "Cleaned backups older than $RETENTION_DAYS days"

echo "Backup complete!"
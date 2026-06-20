#!/bin/bash
# Deploy AI Hub Studio portal to NAB9
set -e

REMOTE_HOST="100.105.27.27"
REMOTE_USER="pepe"
REMOTE_PASS="pepe1234"
REMOTE_DIR="/mnt/seagate/ai-hub-studio"
IMAGE_NAME="ai-hub-studio"

echo "=== Deploying AI Hub Studio to NAB9 ==="

# Create remote directory
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR"

# Copy files
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no -r out/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/out/
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no Dockerfile nginx.conf $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

# Build and run Docker
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cd /mnt/seagate/ai-hub-studio
docker stop ai-hub-studio 2>/dev/null || true
docker rm ai-hub-studio 2>/dev/null || true
docker build -t ai-hub-studio .
docker run -d --name ai-hub-studio --restart unless-stopped -p 3000:3000 ai-hub-studio
echo "=== Portal running at http://100.105.27.27:3000 ==="
ENDSSH
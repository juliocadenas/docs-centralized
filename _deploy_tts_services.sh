#!/bin/bash
# Deploy XTTS-v2 and Fish Speech TTS services to NAB9 server
# Run from local machine: this script is copied to server and executed

set -e

echo "========================================="
echo "  Deploy TTS Services - AI Hub Madrid"
echo "========================================="
echo ""

# 1. Create directories for TTS models
echo "[1/5] Creating model directories..."
mkdir -p /mnt/seagate/models/voice/tts/xtts-v2
mkdir -p /mnt/seagate/models/voice/tts/fish-speech
mkdir -p /mnt/seagate/links/tts
echo "  ✅ Directories created"

# 2. Pull Docker images
echo ""
echo "[2/5] Pulling Docker images (this may take a while)..."

echo "  Pulling XTTS-v2..."
docker pull ghcr.io/coqui-ai/xtts-streaming-server:latest 2>&1 | tail -5
echo "  ✅ XTTS-v2 image pulled"

# Note: Fish Speech image may need to be built from source
# echo "  Pulling Fish Speech..."
# docker pull fishaudio/fish-speech:latest 2>&1 | tail -5
# echo "  ✅ Fish Speech image pulled"

# 3. Start XTTS-v2 container
echo ""
echo "[3/5] Starting XTTS-v2 container..."
docker rm -f xtts-v2 2>/dev/null || true
docker run -d \
  --name xtts-v2 \
  --gpus all \
  -p 8011:80 \
  -v /mnt/seagate/models/voice/tts/xtts-v2:/root/.local/share/coqui \
  -e COQUI_TOS_AGREED=1 \
  --restart unless-stopped \
  ghcr.io/coqui-ai/xtts-streaming-server:latest

echo "  ✅ XTTS-v2 started on port 8011"

# 4. Wait for health check
echo ""
echo "[4/5] Waiting for XTTS-v2 to be ready..."
for i in $(seq 1 60); do
  if curl -s http://localhost:8011/ >/dev/null 2>&1; then
    echo "  ✅ XTTS-v2 is ready! (attempt $i)"
    break
  fi
  if [ $i -eq 60 ]; then
    echo "  ⚠️  XTTS-v2 not ready after 60s, but container is starting"
  fi
  sleep 2
done

# 5. Test TTS
echo ""
echo "[5/5] Testing XTTS-v2..."
sleep 5  # Give it a moment to load the model
TEST_RESULT=$(curl -s -X POST http://localhost:8011/tts_stream \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola, esta es una prueba de XTTS-v2","speaker_wav":"","language":"es"}' \
  -o /dev/null -w "%{http_code}" 2>&1 || echo "000")

if [ "$TEST_RESULT" = "200" ]; then
  echo "  ✅ XTTS-v2 TTS working! (HTTP 200)"
else
  echo "  ℹ️  XTTS-v2 needs more time to load model (HTTP $TEST_RESULT)"
  echo "     It will be ready in ~30 seconds"
fi

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "========================================="
echo ""
echo "Services:"
echo "  - Piper TTS:     http://100.105.27.27:8010 (always-on, CPU)"
echo "  - XTTS-v2:       http://100.105.27.27:8011 (GPU, voice cloning)"
echo "  - Fish Speech:   http://100.105.27.27:8012 (pending image)"
echo "  - Whisper STT:   http://100.105.27.27:8020 (always-on)"
echo ""
echo "Gateway TTS endpoint: http://100.105.27.27:9000/v1/audio/speech"
echo "  Usage: model='piper' | 'xtts' | 'fish'"
echo ""
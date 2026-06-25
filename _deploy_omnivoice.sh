#!/bin/bash
# ============================================================
# OmniVoice Studio - Backend Deployment for AI Hub Madrid
# Instala OmniVoice Studio backend en Docker en el servidor NAB9
# Alternativa open-source a ElevenLabs: 11 motores TTS + 8 ASR + 646 idiomas
# ============================================================

set -e

echo "============================================="
echo "  OmniVoice Studio - AI Hub Madrid"
echo "  11 TTS engines | 8 ASR engines | 646 languages"
echo "============================================="
echo ""

# 1. Crear directorios
echo "[1/6] Creating directories..."
mkdir -p /mnt/seagate/models/voice/omnivoice
mkdir -p /mnt/seagate/links/omnivoice
mkdir -p /mnt/seagate/output/omnivoice
mkdir -p /mnt/seagate/input/omnivoice
echo "  ✅ Directories created"

# 2. Clonar repo de OmniVoice
echo ""
echo "[2/6] Cloning OmniVoice Studio..."
if [ -d "/mnt/seagate/omnivoice-studio" ]; then
    echo "  ℹ️  Repository already exists, pulling latest..."
    cd /mnt/seagate/omnivoice-studio && git pull || true
else
    cd /mnt/seagate
    git clone https://github.com/debpalash/OmniVoice-Studio.git omnivoice-studio
fi
echo "  ✅ Repository ready"

# 3. Construir imagen Docker
echo ""
echo "[3/6] Building Docker image (this may take 5-10 minutes)..."
cd /mnt/seagate/omnivoice-studio

# Usar Dockerfile oficial si existe, sino construir manualmente
if [ -f "docker-compose.yml" ]; then
    echo "  Using official docker-compose..."
    docker compose build backend 2>&1 | tail -10 || true
elif [ -f "Dockerfile" ]; then
    echo "  Using official Dockerfile..."
    docker build -t omnivoice-studio:latest . 2>&1 | tail -10
else
    echo "  ⚠️  No Dockerfile found, creating custom one..."
    cat > /mnt/seagate/omnivoice-studio/Dockerfile.custom << 'DOCKERFILE'
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

WORKDIR /app

# Copy requirements
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt || pip install -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY setup.py ./
COPY pyproject.toml ./

# Expose port
EXPOSE 8030

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8030/health || exit 1

# Start backend
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8030"]
DOCKERFILE
    docker build -t omnivoice-studio:latest -f Dockerfile.custom . 2>&1 | tail -10 || true
fi
echo "  ✅ Docker image built"

# 4. Crear docker-compose para OmniVoice
echo ""
echo "[4/6] Creating Docker Compose config..."
cat > /mnt/seagate/omnivoice-studio/docker-compose.hub.yml << 'EOF'
version: "3.8"

services:
  omnivoice-backend:
    image: omnivoice-studio:latest
    container_name: omnivoice-backend
    restart: unless-stopped
    ports:
      - "8030:8030"
    volumes:
      - /mnt/seagate/models/voice/omnivoice:/app/models
      - /mnt/seagate/output/omnivoice:/app/output
      - /mnt/seagate/input/omnivoice:/app/input
      - /mnt/seagate/links/omnivoice:/app/voices
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - OMNIVOICE_TTS_BACKEND=omnivoice
      - OMNIVOICE_ASR_BACKEND=whisperx
      - HF_HOME=/app/models/huggingface
      - TORCH_HOME=/app/models/torch
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8030/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - ai-hub

networks:
  ai-hub:
    external: true
    name: ai-hub-network
EOF
echo "  ✅ Docker Compose config created"

# 5. Iniciar el servicio
echo ""
echo "[5/6] Starting OmniVoice backend..."
docker rm -f omnivoice-backend 2>/dev/null || true

# Intentar con compose, si falla usar docker run directo
docker compose -f /mnt/seagate/omnivoice-studio/docker-compose.hub.yml up -d 2>&1 | tail -5 || \
docker run -d \
    --name omnivoice-backend \
    --gpus all \
    -p 8030:8030 \
    -v /mnt/seagate/models/voice/omnivoice:/app/models \
    -v /mnt/seagate/output/omnivoice:/app/output \
    -v /mnt/seagate/input/omnivoice:/app/input \
    -v /mnt/seagate/links/omnivoice:/app/voices \
    -e CUDA_VISIBLE_DEVICES=0 \
    -e OMNIVOICE_TTS_BACKEND=omnivoice \
    -e OMNIVOICE_ASR_BACKEND=whisperx \
    -e HF_HOME=/app/models/huggingface \
    -e TORCH_HOME=/app/models/torch \
    --restart unless-stopped \
    omnivoice-studio:latest

echo "  ✅ OmniVoice backend started on port 8030"

# 6. Health check
echo ""
echo "[6/6] Waiting for OmniVoice to be ready..."
for i in $(seq 1 60); do
    if curl -s http://localhost:8030/health >/dev/null 2>&1; then
        echo "  ✅ OmniVoice is ready! (attempt $i)"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "  ⚠️  OmniVoice not ready after 120s"
        echo "     Check logs: docker logs omnivoice-backend"
    fi
    sleep 2
done

echo ""
echo "============================================="
echo "  OmniVoice Studio Deployed!"
echo "============================================="
echo ""
echo "Endpoints:"
echo "  Backend API:  http://100.105.27.27:8030"
echo "  Health:       http://100.105.27.27:8030/health"
echo "  TTS:          POST http://100.105.27.27:8030/api/tts"
echo "  Clone:        POST http://100.105.27.27:8030/api/voice/clone"
echo "  ASR:          POST http://100.105.27.27:8030/api/asr"
echo ""
echo "Gateway integration:"
echo "  POST http://100.105.27.27:9000/v1/audio/speech?model=omnivoice"
echo ""
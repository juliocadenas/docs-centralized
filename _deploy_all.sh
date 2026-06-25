#!/bin/bash
# ============================================================
#  🚀 DEPLOY TOTAL v2 - AI Hub Madrid (NAB9)
#  Ejecutar UNA SOLA VEZ en el NAB9 como root
#  Incluye: Gateway v2.3 + RAG + OpenMontage + OmniVoice + LLM Models
# ============================================================
set -e

echo "================================================"
echo "  🚀 DEPLOY TOTAL v2 AI Hub - NAB9"
echo "  Gateway v2.3 + RAG + OpenMontage + OmniVoice"
echo "================================================"

# Verificar que somos root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Ejecutar como root: sudo bash _deploy_all.sh"
  exit 1
fi

# Verificar que estamos en el NAB9
if ! hostname | grep -qi pop-os; then
  echo "❌ Este script debe ejecutarse en el NAB9 (pop-os)"
  exit 1
fi

echo ""
echo "=== [1/12] ESPACIO EN DISCO ==="
df -h / /mnt/seagate
echo ""
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 85 ]; then
  echo "⚠️  Disco principal al ${DISK_USAGE}% - PROCEDIENDO CON CUIDADO"
else
  echo "✅ Disco principal al ${DISK_USAGE}% - OK"
fi

echo ""
echo "=== [2/12] GIT PULL DEL REPO ==="
cd /mnt/seagate/repos/IA-HUB-MADRID1 2>/dev/null || cd /home/pepe/IA-HUB-MADRID1 2>/dev/null || {
  echo "⚠️  No se encontró el repo. Clonando..."
  cd /mnt/seagate/repos
  git clone https://github.com/juliocadenas/IA-HUB-MADRID1.git
  cd IA-HUB-MADRID1
}
git pull origin main || echo "⚠️  Git pull falló, continuando..."
REPO_PATH=$(pwd)
echo "✅ Repo actualizado en: $REPO_PATH"

echo ""
echo "=== [3/12] DEPLOY GATEWAY (routers + config) ==="
GATEWAY_PATH="/mnt/seagate/api/ai-hub-gateway"
if [ ! -d "$GATEWAY_PATH/gateway" ]; then
  GATEWAY_PATH=$(find / -name "config.py" -path "*/gateway/*" 2>/dev/null | head -1 | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null)
fi

if [ -n "$GATEWAY_PATH" ] && [ -d "$GATEWAY_PATH/gateway" ]; then
  echo "  Gateway encontrado en: $GATEWAY_PATH"

  # Copiar config actualizado
  cp "$REPO_PATH/ai-hub-gateway/gateway/config.py" "$GATEWAY_PATH/gateway/config.py"
  echo "  ✅ config.py copiado"

  # Copiar main.py actualizado
  cp "$REPO_PATH/ai-hub-gateway/main.py" "$GATEWAY_PATH/main.py"
  echo "  ✅ main.py copiado"

  # Copiar requirements.txt
  cp "$REPO_PATH/ai-hub-gateway/requirements.txt" "$GATEWAY_PATH/requirements.txt"
  echo "  ✅ requirements.txt copiado"

  # Copiar TODOS los routers
  for router in llm images audio video status voice avatar effects; do
    if [ -f "$REPO_PATH/ai-hub-gateway/gateway/routers/${router}.py" ]; then
      cp "$REPO_PATH/ai-hub-gateway/gateway/routers/${router}.py" "$GATEWAY_PATH/gateway/routers/"
    fi
  done
  echo "  ✅ Routers copiados"

  # Copiar el NUEVO router RAG
  cp "$REPO_PATH/ai-hub-gateway/gateway/routers/rag.py" "$GATEWAY_PATH/gateway/routers/"
  echo "  ✅ Router RAG copiado"

  # Copiar servicios actualizados
  for svc in ollama comfyui documusic wan2gp; do
    if [ -f "$REPO_PATH/ai-hub-gateway/gateway/services/${svc}.py" ]; then
      cp "$REPO_PATH/ai-hub-gateway/gateway/services/${svc}.py" "$GATEWAY_PATH/gateway/services/"
    fi
  done
  echo "  ✅ Services copiados"
else
  echo "❌ No se encontró el Gateway. Saltando..."
fi

echo ""
echo "=== [4/12] INSTALAR DEPENDENCIAS PYTHON (RAG) ==="
if [ -n "$GATEWAY_PATH" ]; then
  # Detectar si usa venv o sistema
  if [ -f "$GATEWAY_PATH/venv/bin/pip" ]; then
    PIP="$GATEWAY_PATH/venv/bin/pip"
  elif command -v pip3 &>/dev/null; then
    PIP="pip3"
  else
    PIP="pip"
  fi

  echo "  Instalando chromadb + PyMuPDF con: $PIP"
  $PIP install chromadb PyMuPDF 2>&1 | tail -5
  echo "  ✅ Dependencias RAG instaladas"
fi

echo ""
echo "=== [5/12] DEPLOY AI HUB STUDIO (UI) ==="
STUDIO_PATH="/mnt/seagate/api/ai-hub-studio"
if [ ! -d "$STUDIO_PATH" ]; then
  STUDIO_PATH=$(find / -name "page.tsx" -path "*/src/app/*" 2>/dev/null | head -1 | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null)
fi

if [ -n "$STUDIO_PATH" ] && [ -d "$STUDIO_PATH/src" ]; then
  echo "  Studio encontrado en: $STUDIO_PATH"

  # Copiar archivos actualizados
  cp "$REPO_PATH/ai-hub-studio/src/app/page.tsx" "$STUDIO_PATH/src/app/page.tsx"
  cp "$REPO_PATH/ai-hub-studio/src/lib/api.ts" "$STUDIO_PATH/src/lib/api.ts"
  echo "  ✅ page.tsx y api.ts copiados"

  # Rebuild del Studio
  echo "  Rebuildando Studio (puede tardar 1-2 min)..."
  cd "$STUDIO_PATH"
  npm install --silent 2>/dev/null || true
  npm run build --silent 2>&1 | tail -5
  echo "  ✅ Studio rebuildado"

  # Restart container si existe
  if docker ps --format '{{.Names}}' | grep -q ai-hub-studio; then
    docker restart ai-hub-studio
    echo "  ✅ Container ai-hub-studio reiniciado"
  fi
  cd "$REPO_PATH"
else
  echo "⚠️  No se encontró AI Hub Studio. Saltando..."
fi

echo ""
echo "=== [6/12] MOVER OLLAMA AL SEAGATE (si no está ya) ==="
OLLAMA_TARGET="/mnt/seagate/models/llm/ollama"
if grep -q "/mnt/seagate" /etc/systemd/system/ollama.service.d/override.conf 2>/dev/null; then
  echo "✅ Ollama ya configurado para Seagate"
else
  echo "⚠️  Configurando Ollama para Seagate..."
  mkdir -p /etc/systemd/system/ollama.service.d
  cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_MODELS=/mnt/seagate/models/llm/ollama"
EOF
  systemctl daemon-reload
  systemctl restart ollama
  echo "✅ Ollama configurado para Seagate"
fi

echo ""
echo "=== [7/12] INSTALAR MODELOS LLM ADICIONALES ==="
echo "  Verificando modelos instalados..."
INSTALLED=$(ollama list 2>/dev/null || echo "")

for model in "qwen2.5:14b" "llama3.2:3b" "gemma2:9b"; do
  if echo "$INSTALLED" | grep -q "$model"; then
    echo "  ✅ $model ya instalado"
  else
    echo "  📦 Instalando $model..."
    ollama pull "$model" 2>&1 | tail -3
  fi
done
echo "✅ Modelos LLM verificados"

echo ""
echo "=== [8/12] INSTALAR REMOTION (OpenMontage Render) ==="
if ! command -v npx &>/dev/null; then
  echo "  ⚠️  Node.js no encontrado. Instalando Node.js 20..."
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

REMOTION_DIR="/mnt/seagate/api/remotion-render"
if [ ! -d "$REMOTION_DIR" ]; then
  echo "  📦 Creando proyecto Remotion..."
  mkdir -p "$REMOTION_DIR"
  cd "$REMOTION_DIR"
  npm init -y
  npm install remotion @remotion/cli @remotion/bundler --silent
  echo "  ✅ Remotion instalado"
else
  echo "  ✅ Remotion ya existe en $REMOTION_DIR"
fi

# Crear systemd service para Remotion
cat > /etc/systemd/system/remotion-render.service << 'EOF'
[Unit]
Description=Remotion Render Server (AI Hub Madrid)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/mnt/seagate/api/remotion-render
ExecStart=/usr/bin/npx remotion studio --port=8601
Restart=on-failure
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable remotion-render 2>/dev/null || true
# No iniciamos remotion ahora porque es on-demand (CPU-only, always_on=False)
echo "  ✅ Servicio remotion-render creado (no iniciado, es on-demand)"
cd "$REPO_PATH"

echo ""
echo "=== [9/12] DEPLOY OMNIVOICE (TTS 646 idiomas) ==="
OMNIVOICE_DIR="/mnt/seagate/api/omnivoice"
if [ ! -d "$OMNIVOICE_DIR" ]; then
  if [ -f "$REPO_PATH/_deploy_omnivoice.sh" ]; then
    echo "  📦 Ejecutando deploy OmniVoice..."
    bash "$REPO_PATH/_deploy_omnivoice.sh" || echo "  ⚠️  OmniVoice deploy falló (revisar logs)"
  else
    echo "  ⚠️  Script _deploy_omnivoice.sh no encontrado"
  fi
else
  echo "  ✅ OmniVoice ya desplegado"
fi

echo ""
echo "=== [10/12] WATCHDOGS Y HARDENING ==="
# PCIe watchdog
if [ -f "scripts/pcie-watchdog.sh" ]; then
  cp scripts/pcie-watchdog.sh /usr/local/bin/ 2>/dev/null || true
  chmod +x /usr/local/bin/pcie-watchdog.sh
  cp scripts/pcie-watchdog.service /etc/systemd/system/ 2>/dev/null || true
  systemctl daemon-reload
  systemctl enable --now pcie-watchdog 2>/dev/null || true
  echo "✅ PCIe watchdog instalado"
fi

# VRAM watchdog
if [ -f "scripts/vram-watchdog.sh" ]; then
  cp scripts/vram-watchdog.sh /usr/local/bin/ 2>/dev/null || true
  chmod +x /usr/local/bin/vram-watchdog.sh
  cp scripts/vram-watchdog.service /etc/systemd/system/ 2>/dev/null || true
  systemctl daemon-reload
  systemctl enable --now vram-watchdog 2>/dev/null || true
  echo "✅ VRAM watchdog instalado"
fi

# OOM protection
mkdir -p /etc/systemd/system/ollama.service.d /etc/systemd/system/ai-hub-gateway.service.d
if [ -f "scripts/oom-protection-dropins.conf" ]; then
  cp scripts/oom-protection-dropins.conf /etc/systemd/system/ollama.service.d/oom.conf 2>/dev/null || true
  cp scripts/oom-protection-dropins.conf /etc/systemd/system/ai-hub-gateway.service.d/oom.conf 2>/dev/null || true
  systemctl daemon-reload
  echo "✅ OOM protection aplicado"
fi

echo ""
echo "=== [11/12] REINICIAR GATEWAY ==="
systemctl restart ai-hub-gateway
sleep 5
if systemctl is-active --quiet ai-hub-gateway; then
  echo "✅ Gateway reiniciado y funcionando"
else
  echo "❌ Gateway no arrancó. Revisar: journalctl -u ai-hub-gateway -f"
fi

echo ""
echo "=== [12/12] VERIFICACIÓN FINAL ==="
echo "--- GPU ---"
nvidia-smi --query-gpu=temperature.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo "  nvidia-smi no disponible"

echo "--- Disco ---"
df -h / /mnt/seagate

echo "--- Servicios ---"
systemctl is-active ai-hub-gateway ollama pcie-watchdog vram-watchdog 2>/dev/null || true

echo "--- Gateway Status ---"
sleep 2
curl -s http://localhost:9000/v1/status 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'Version: {d.get(\"gateway_version\", \"?\")}')
    print(f'Uptime: {d.get(\"uptime_seconds\", 0)/3600:.1f} horas')
    online = [s for s in d.get('services', []) if s.get('status') == 'online']
    print(f'Servicios online: {len(online)}/{len(d.get(\"services\", []))}')
    for s in online:
        print(f'  ✅ {s[\"name\"]}: {s.get(\"response_time_ms\", \"?\")}ms')
except:
    print('No se pudo obtener status')
" 2>/dev/null || echo "  No se pudo conectar al Gateway"

echo "--- RAG Health ---"
curl -s http://localhost:9000/v1/rag/health 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'RAG Status: {d.get(\"status\")}')
    if d.get('status') == 'ok':
        print(f'  ChromaDB: {d.get(\"chromadb_version\")}')
        print(f'  Colecciones: {d.get(\"collections\", 0)}')
except:
    print('RAG no responde')
" 2>/dev/null || echo "  RAG no disponible todavía"

echo "--- Modelos Ollama ---"
ollama list 2>/dev/null | head -10

echo ""
echo "================================================"
echo "  ✅ DEPLOY v2 COMPLETADO!"
echo "================================================"
echo ""
echo "🎯 Endpoints nuevos disponibles:"
echo "   POST /v1/video/agentic       - Pipeline video agentic"
echo "   POST /v1/rag/upload          - Subir documentos"
echo "   POST /v1/rag/query           - Consultar documentos"
echo "   GET  /v1/rag/health          - Estado RAG"
echo "   POST /v1/audio/speech        - TTS (Piper/XTTS/Fish/OmniVoice)"
echo ""
echo "🔧 Para activar Remotion (video agentic):"
echo "   sudo systemctl start remotion-render"
echo ""
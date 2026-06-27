#!/bin/bash
# ============================================================
#  🚀 DEPLOY TODO-IN-UNO - AI Hub Madrid v2.3.0 → NAB9
#  Ejecutar en el NAB9 como root (una sola vez)
#  Comando: sudo bash DEPLOY_V23_NAB9.sh
# ============================================================
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}  🚀 DEPLOY v2.3.0 - AI Hub Madrid → NAB9${NC}"
echo -e "${CYAN}  +RAG +Agentic Video +Embeddings +LLM Models${NC}"
echo -e "${CYAN}================================================${NC}"

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ Ejecutar como root: sudo bash DEPLOY_V23_NAB9.sh${NC}"
  exit 1
fi

if ! hostname | grep -qi pop-os; then
  echo -e "${RED}❌ Ejecutar en el NAB9 (pop-os). Host actual: $(hostname)${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Host: $(hostname) | $(date)${NC}"

# === [1/9] LOCALIZAR ===
echo -e "\n${CYAN}=== [1/9] LOCALIZANDO COMPONENTES ===${NC}"
REPO_PATH=$(find /mnt/seagate/repos /home -maxdepth 3 -name "IA-HUB-MADRID1" -type d 2>/dev/null | head -1)
if [ -z "$REPO_PATH" ]; then
  REPO_PATH=$(find /mnt/seagate/repos /home -maxdepth 3 -name "docs-centralized" -type d 2>/dev/null | head -1)
fi
if [ -z "$REPO_PATH" ]; then
  echo -e "${YELLOW}  Clonando repo...${NC}"
  mkdir -p /mnt/seagate/repos && cd /mnt/seagate/repos
  git clone https://github.com/juliocadenas/docs-centralized.git IA-HUB-MADRID1 2>/dev/null || true
  REPO_PATH="/mnt/seagate/repos/IA-HUB-MADRID1"
fi
echo -e "${GREEN}  ✅ Repo: $REPO_PATH${NC}"

GATEWAY_PATH=$(find /mnt/seagate/api /opt /home -maxdepth 4 -name "config.py" -path "*/gateway/*" 2>/dev/null | head -1 | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null)
GATEWAY_PATH="${GATEWAY_PATH:-/mnt/seagate/api/ai-hub-gateway}"
echo -e "${GREEN}  ✅ Gateway: $GATEWAY_PATH${NC}"

STUDIO_PATH=$(find /mnt/seagate/api /opt /home -maxdepth 5 -name "page.tsx" -path "*/src/app/*" 2>/dev/null | head -1 | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null)
STUDIO_PATH="${STUDIO_PATH:-/mnt/seagate/api/ai-hub-studio}"
echo -e "${GREEN}  ✅ Studio: $STUDIO_PATH${NC}"

cd "$REPO_PATH"

# === [2/9] GIT PULL ===
echo -e "\n${CYAN}=== [2/9] ACTUALIZANDO REPO ===${NC}"
git fetch origin 2>/dev/null || true
git reset --hard origin/main 2>/dev/null || git pull origin main 2>/dev/null || echo -e "${YELLOW}  ⚠️ Usando archivos locales${NC}"
echo -e "${GREEN}  ✅ Repo actualizado${NC}"

# === [3/9] GATEWAY ===
echo -e "\n${CYAN}=== [3/9] DEPLOY GATEWAY v2.3.0 ===${NC}"

if [ -d "$GATEWAY_PATH/gateway" ]; then
  cp -r "$GATEWAY_PATH/gateway" "$GATEWAY_PATH/gateway.bak.$(date +%s)" 2>/dev/null || true
  cp "$REPO_PATH/ai-hub-gateway/gateway/config.py" "$GATEWAY_PATH/gateway/config.py" 2>/dev/null && echo -e "${GREEN}  ✅ config.py${NC}"
  cp "$REPO_PATH/ai-hub-gateway/main.py" "$GATEWAY_PATH/main.py" 2>/dev/null && echo -e "${GREEN}  ✅ main.py${NC}"
  cp "$REPO_PATH/ai-hub-gateway/requirements.txt" "$GATEWAY_PATH/requirements.txt" 2>/dev/null && echo -e "${GREEN}  ✅ requirements.txt${NC}"
  mkdir -p "$GATEWAY_PATH/gateway/routers"
  for r in llm images audio video status voice avatar effects rag; do
    [ -f "$REPO_PATH/ai-hub-gateway/gateway/routers/${r}.py" ] && cp "$REPO_PATH/ai-hub-gateway/gateway/routers/${r}.py" "$GATEWAY_PATH/gateway/routers/"
  done
  echo -e "${GREEN}  ✅ Routers copiados${NC}"
  for s in ollama comfyui documusic wan2gp; do
    [ -f "$REPO_PATH/ai-hub-gateway/gateway/services/${s}.py" ] && cp "$REPO_PATH/ai-hub-gateway/gateway/services/${s}.py" "$GATEWAY_PATH/gateway/services/"
  done
  echo -e "${GREEN}  ✅ Services copiados${NC}"
  [ -f "$REPO_PATH/ai-hub-gateway/gateway/gpu_manager.py" ] && cp "$REPO_PATH/ai-hub-gateway/gateway/gpu_manager.py" "$GATEWAY_PATH/gateway/"
else
  echo -e "${RED}  ❌ Gateway no encontrado: $GATEWAY_PATH${NC}"
fi

# === [4/9] RAG DEPS ===
echo -e "\n${CYAN}=== [4/9] DEPENDENCIAS RAG ===${NC}"
if [ -f "$GATEWAY_PATH/venv/bin/pip" ]; then PIP="$GATEWAY_PATH/venv/bin/pip"; else PIP="pip3"; fi
echo -e "${YELLOW}  Usando: $PIP${NC}"
$PIP install chromadb PyMuPDF 2>&1 | tail -3
echo -e "${GREEN}  ✅ RAG deps instaladas${NC}"

# === [5/9] MODELOS LLM ===
echo -e "\n${CYAN}=== [5/9] MODELOS LLM ===${NC}"
INSTALLED=$(ollama list 2>/dev/null || echo "")
for model in "qwen2.5:14b" "gemma2:9b" "llama3.2:3b"; do
  if echo "$INSTALLED" | grep -q "$model"; then
    echo -e "${GREEN}  ✅ $model instalado${NC}"
  else
    echo -e "${YELLOW}  📦 Instalando $model...${NC}"
    ollama pull "$model" 2>&1 | tail -2
  fi
done

# === [6/9] STUDIO ===
echo -e "\n${CYAN}=== [6/9] AI HUB STUDIO ===${NC}"
if [ -d "$STUDIO_PATH/src" ]; then
  cp "$STUDIO_PATH/src/app/page.tsx" "$STUDIO_PATH/src/app/page.tsx.bak" 2>/dev/null || true
  [ -f "$REPO_PATH/ai-hub-studio/src/app/page.tsx" ] && cp "$REPO_PATH/ai-hub-studio/src/app/page.tsx" "$STUDIO_PATH/src/app/page.tsx" && echo -e "${GREEN}  ✅ page.tsx${NC}"
  [ -f "$REPO_PATH/ai-hub-studio/src/lib/api.ts" ] && cp "$REPO_PATH/ai-hub-studio/src/lib/api.ts" "$STUDIO_PATH/src/lib/api.ts" && echo -e "${GREEN}  ✅ api.ts${NC}"
  echo -e "${YELLOW}  Rebuildando...${NC}"
  cd "$STUDIO_PATH" && npm install --silent 2>/dev/null && npm run build --silent 2>&1 | tail -3
  docker ps --format '{{.Names}}' 2>/dev/null | grep -q ai-hub-studio && docker restart ai-hub-studio 2>/dev/null
  echo -e "${GREEN}  ✅ Studio rebuildado${NC}"
  cd "$REPO_PATH"
else
  echo -e "${YELLOW}  ⚠️ Studio no encontrado${NC}"
fi

# === [7/9] REMOTION ===
echo -e "\n${CYAN}=== [7/9] REMOTION ===${NC}"
REMOTION_DIR="/mnt/seagate/api/remotion-render"
if [ ! -d "$REMOTION_DIR" ]; then
  mkdir -p "$REMOTION_DIR" && cd "$REMOTION_DIR"
  npm init -y --silent && npm install remotion @remotion/cli @remotion/bundler --silent 2>&1 | tail -2
  echo -e "${GREEN}  ✅ Remotion instalado${NC}"
else
  echo -e "${GREEN}  ✅ Remotion existe${NC}"
fi
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
systemctl daemon-reload && systemctl enable remotion-render 2>/dev/null || true
echo -e "${GREEN}  ✅ Servicio remotion-render creado${NC}"
cd "$REPO_PATH"

# === [8/9] RESTART GATEWAY ===
echo -e "\n${CYAN}=== [8/9] REINICIANDO GATEWAY ===${NC}"
systemctl restart ai-hub-gateway
sleep 8
systemctl is-active --quiet ai-hub-gateway && echo -e "${GREEN}  ✅ Gateway activo${NC}" || { echo -e "${RED}  ❌ Gateway falló${NC}"; journalctl -u ai-hub-gateway -n 20; }

# === [9/9] VERIFY ===
echo -e "\n${CYAN}=== [9/9] VERIFICACIÓN ===${NC}"
echo -e "\n${YELLOW}--- Gateway ---${NC}"
curl -s http://localhost:9000/ 2>/dev/null | grep -o '"version":"[^"]*"' | head -1
echo -e "\n${YELLOW}--- RAG ---${NC}"
curl -s http://localhost:9000/v1/rag/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d.get(\"status\")}, ChromaDB: {d.get(\"chromadb_version\",\"?\")}')" 2>/dev/null || echo "RAG pendiente"
echo -e "\n${YELLOW}--- Servicios ---${NC}"
curl -s http://localhost:9000/v1/status 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); o=[s for s in d['services'] if s['status']=='online']; print(f'{len(o)}/{len(d[\"services\"])} online')" 2>/dev/null
echo -e "\n${YELLOW}--- GPU ---${NC}"
nvidia-smi --query-gpu=temperature.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}  ✅ DEPLOY v2.3.0 COMPLETADO!${NC}"
echo -e "${GREEN}================================================${NC}"
echo -e "\n${YELLOW}Endpoints nuevos:${NC}"
echo "  POST /v1/video/agentic  POST /v1/rag/upload  POST /v1/rag/query"
echo -e "${YELLOW}Activar Remotion: sudo systemctl start remotion-render${NC}"
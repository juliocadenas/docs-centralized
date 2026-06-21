#!/bin/bash
# ============================================================
# DEPLOY SCRIPT - Ejecutar en el NAB9 (100.105.27.27)
# Copia este archivo al servidor y ejecútalo con:
#   bash _deploy_on_server.sh
# ============================================================
set -e

echo "============================================================"
echo "  DEPLOY AI HUB GATEWAY - NAB9"
echo "============================================================"

GATEWAY_DIR="/mnt/seagate/api/ai-hub-gateway"
REPO_DIR="/mnt/seagate/api/IA-HUB-MADRID1"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. Verificar que estamos en el servidor correcto
echo ""
info "1. Verificando servidor..."
HOSTNAME=$(hostname)
if [[ "$HOSTNAME" != *"nab9"* ]] && [[ "$HOSTNAME" != *"madrid"* ]]; then
    warn "Hostname: $HOSTNAME (esperado: nab9/madrid)"
    warn "¿Seguro que estás en el servidor correcto? (Ctrl+C para abortar)"
    read -r -t 5 || true
fi
info "   Hostname: $HOSTNAME"

# 2. Clonar o actualizar el repo
echo ""
info "2. Actualizando repositorio..."
if [ -d "$REPO_DIR/.git" ]; then
    info "   Repo existe, haciendo pull..."
    cd "$REPO_DIR"
    git pull origin main 2>/dev/null || warn "   No se pudo hacer pull (sin internet?), usando código local"
else
    info "   Clonando repo..."
    mkdir -p "$(dirname $REPO_DIR)"
    git clone https://github.com/juliocadenas/IA-HUB-MADRID1.git "$REPO_DIR" 2>/dev/null || {
        warn "   No se pudo clonar. ¿Usar código local de $GATEWAY_DIR?"
    }
fi

# 3. Sincronizar archivos del gateway
echo ""
info "3. Sincronizando archivos del gateway..."
SOURCE_DIR="${REPO_DIR}/ai-hub-gateway"
if [ ! -d "$SOURCE_DIR" ]; then
    SOURCE_DIR="$GATEWAY_DIR"
fi

# Copiar routers
mkdir -p "$GATEWAY_DIR/gateway/routers"
mkdir -p "$GATEWAY_DIR/gateway/services"
mkdir -p "$GATEWAY_DIR/gateway/models"
mkdir -p "$GATEWAY_DIR/services"

for file in config.py __init__.py gpu_manager.py; do
    if [ -f "$SOURCE_DIR/gateway/$file" ]; then
        cp "$SOURCE_DIR/gateway/$file" "$GATEWAY_DIR/gateway/$file"
        info "   ✅ gateway/$file"
    fi
done

for router in llm.py images.py audio.py video.py status.py voice.py avatar.py effects.py __init__.py; do
    if [ -f "$SOURCE_DIR/gateway/routers/$router" ]; then
        cp "$SOURCE_DIR/gateway/routers/$router" "$GATEWAY_DIR/gateway/routers/$router"
        info "   ✅ gateway/routers/$router"
    fi
done

for svc in ollama.py comfyui.py documusic.py wan2gp.py __init__.py; do
    if [ -f "$SOURCE_DIR/gateway/services/$svc" ]; then
        cp "$SOURCE_DIR/gateway/services/$svc" "$GATEWAY_DIR/gateway/services/$svc"
        info "   ✅ gateway/services/$svc"
    fi
done

if [ -f "$SOURCE_DIR/gateway/models/schemas.py" ]; then
    cp "$SOURCE_DIR/gateway/models/schemas.py" "$GATEWAY_DIR/gateway/models/schemas.py"
    info "   ✅ gateway/models/schemas.py"
fi

if [ -f "$SOURCE_DIR/docker-compose.yml" ]; then
    cp "$SOURCE_DIR/docker-compose.yml" "$GATEWAY_DIR/docker-compose.yml"
    info "   ✅ docker-compose.yml"
fi

# Copiar servicios Docker
if [ -d "$SOURCE_DIR/services" ]; then
    for svc_dir in "$SOURCE_DIR/services"/*/; do
        svc_name=$(basename "$svc_dir")
        mkdir -p "$GATEWAY_DIR/services/$svc_name"
        cp -r "$svc_dir"* "$GATEWAY_DIR/services/$svc_name/" 2>/dev/null || true
        info "   ✅ services/$svc_name"
    done
fi

# 4. Reiniciar gateway
echo ""
info "4. Reiniciando AI Hub Gateway..."
sudo systemctl restart ai-hub-gateway
sleep 3

# 5. Verificar estado
echo ""
info "5. Verificando estado del gateway..."
sleep 2

STATUS=$(curl -s http://localhost:9000/v1/status 2>/dev/null)
if [ -z "$STATUS" ]; then
    error "   Gateway no responde!"
    error "   Revisa: sudo journalctl -u ai-hub-gateway -n 20"
else
    echo "$STATUS" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Status: {d[\"status\"]}')
print(f'  Uptime: {d[\"uptime_seconds\"]:.0f}s')
online = [s for s in d['services'] if s['status'] == 'online']
offline = [s for s in d['services'] if s['status'] != 'online']
print(f'  Online ({len(online)}):')
for s in online:
    rt = f'{s[\"response_time_ms\"]:.0f}ms' if s.get('response_time_ms') else 'N/A'
    print(f'    ✅ {s[\"name\"]:30s} {rt}')
print(f'  Offline ({len(offline)}):')
for s in offline:
    print(f'    ❌ {s[\"name\"]:30s} {s.get(\"error\",\"\")[:40]}')
" 2>/dev/null || warn "   No se pudo parsear el status"
fi

# 6. Modelos disponibles
echo ""
info "6. Modelos disponibles..."
curl -s http://localhost:9000/v1/models 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Total: {len(d[\"data\"])} modelos')
for m in d['data']:
    print(f'    📦 {m[\"id\"]:30s} ({m.get(\"type\",\"unknown\")})')
" 2>/dev/null || warn "   No se pudo obtener lista de modelos"

# 7. Modelos Ollama instalados
echo ""
info "7. Modelos Ollama instalados..."
curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
models = d.get('models', [])
print(f'  Total: {len(models)}')
for m in models:
    size_gb = m.get('size', 0) / 1024**3
    print(f'    🧠 {m[\"name\"]:30s} {size_gb:.1f}GB')
" 2>/dev/null || warn "   Ollama no responde"

echo ""
echo "============================================================"
info "DEPLOY COMPLETADO!"
echo "  Gateway:  http://100.105.27.27:9000/v1/status"
echo "  Docs:     http://100.105.27.27:9000/docs"
echo "  Logs:     sudo journalctl -u ai-hub-gateway -f"
echo "============================================================"
#!/bin/bash
# ============================================================
#  🔧 DEPLOY RÁPIDO - Fix generación de video Wan2GP
#  Ejecutar en el NAB9: sudo bash DEPLOY_VIDEO_FIX.sh
# ============================================================
set -e

echo "🔧 Deploy fix video Wan2GP..."

# Encontrar repo y gateway
REPO_PATH=$(find /mnt/seagate/repos /home -maxdepth 3 -name "IA-HUB-MADRID1" -type d 2>/dev/null | head -1)
[ -z "$REPO_PATH" ] && REPO_PATH=$(find /mnt/seagate/repos /home -maxdepth 3 -name "docs-centralized" -type d 2>/dev/null | head -1)

GATEWAY_PATH=$(find /mnt/seagate/api /opt /home -maxdepth 4 -name "config.py" -path "*/gateway/*" 2>/dev/null | head -1 | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null)
GATEWAY_PATH="${GATEWAY_PATH:-/mnt/seagate/api/ai-hub-gateway}"

echo "  Repo: $REPO_PATH"
echo "  Gateway: $GATEWAY_PATH"

# Git pull
cd "$REPO_PATH"
git fetch origin 2>/dev/null || true
git reset --hard origin/main 2>/dev/null || git pull origin main 2>/dev/null
echo "✅ Código actualizado"

# Copiar los 4 archivos cambiados
cp "$REPO_PATH/ai-hub-gateway/gateway/services/wan2gp.py" "$GATEWAY_PATH/gateway/services/wan2gp.py"
cp "$REPO_PATH/ai-hub-gateway/gateway/routers/video.py" "$GATEWAY_PATH/gateway/routers/video.py"
cp "$REPO_PATH/ai-hub-gateway/gateway/models/schemas.py" "$GATEWAY_PATH/gateway/models/schemas.py"
cp "$REPO_PATH/ai-hub-gateway/requirements.txt" "$GATEWAY_PATH/requirements.txt"
echo "✅ Archivos copiados"

# Instalar gradio_client (nueva dependencia)
echo "📦 Instalando gradio_client..."
if [ -f "$GATEWAY_PATH/venv/bin/pip" ]; then
    "$GATEWAY_PATH/venv/bin/pip" install "gradio_client>=1.3.0" 2>&1 | tail -3
else
    pip3 install "gradio_client>=1.3.0" 2>&1 | tail -3
fi
echo "✅ Dependencias instaladas"

# Reiniciar gateway
systemctl restart ai-hub-gateway
sleep 5

if systemctl is-active --quiet ai-hub-gateway; then
    echo "✅ Gateway reiniciado correctamente"
    echo ""
    echo "🧪 Probando estado..."
    curl -s --max-time 10 http://localhost:9000/v1/status | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Gateway: {d[\"gateway_version\"]}')
w=[s for s in d['services'] if s['name']=='wan2gp'][0]
print(f'Wan2GP: {w[\"status\"]}')
" 2>/dev/null
    echo ""
    echo "✅ ¡Listo! Prueba crear un video en http://localhost:3000"
else
    echo "❌ Gateway falló al iniciar"
    journalctl -u ai-hub-gateway -n 20 --no-pager
fi
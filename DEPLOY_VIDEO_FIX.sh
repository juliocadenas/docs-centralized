#!/bin/bash
# ============================================================
#  🔧 DEPLOY RÁPIDO - Fix generación de video Wan2GP
#  Usa HTTP Gradio 5.x API directo (sin gradio_client)
#  Ejecutar en el NAB9: sudo bash DEPLOY_VIDEO_FIX.sh
# ============================================================
set -e

echo "🔧 Deploy fix video Wan2GP (HTTP Gradio API)..."

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

# Copiar solo el archivo cambiado (wan2gp.py usa httpx puro, no necesita nuevas deps)
cp "$REPO_PATH/ai-hub-gateway/gateway/services/wan2gp.py" "$GATEWAY_PATH/gateway/services/wan2gp.py"
echo "✅ wan2gp.py copiado"

# Reiniciar gateway
systemctl restart ai-hub-gateway
sleep 5

if systemctl is-active --quiet ai-hub-gateway; then
    echo "✅ Gateway reiniciado correctamente"
    echo ""
    echo "🧪 Probando video generation..."
    # Test que el endpoint responde
    STATUS=$(curl -s --max-time 10 http://localhost:9000/v1/video/generations \
        -X POST -H "Content-Type: application/json" \
        -d '{"prompt":"test","model":"wan2.1","resolution":"480p","duration_seconds":3}' \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','error'))" 2>/dev/null || echo "timeout")
    echo "  Video endpoint status: $STATUS"
    echo ""
    echo "✅ ¡Listo! Prueba crear un video en http://localhost:3000"
else
    echo "❌ Gateway falló al iniciar"
    journalctl -u ai-hub-gateway -n 20 --no-pager
fi
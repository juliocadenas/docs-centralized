#!/bin/bash
# ============================================================
#  🚀 DEPLOY TOTAL - AI Hub Madrid (NAB9)
#  Ejecutar UNA SOLA VEZ en el NAB9 como root
#  Hace: git pull + config deploy + mover modelos + watchdogs
# ============================================================
set -e

echo "================================================"
echo "  🚀 DEPLOY TOTAL AI Hub - NAB9"
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
echo "=== [1/8] ESPACIO EN DISCO ==="
df -h / /mnt/seagate
echo ""
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 85 ]; then
  echo "⚠️  Disco principal al ${DISK_USAGE}% - PROCEEDIENDO CON CUIDADO"
else
  echo "✅ Disco principal al ${DISK_USAGE}% - OK"
fi

echo ""
echo "=== [2/8] GIT PULL DEL REPO ==="
cd /mnt/seagate/repos/IA-HUB-MADRID1 2>/dev/null || cd /home/pepe/IA-HUB-MADRID1 2>/dev/null || {
  echo "⚠️  No se encontró el repo. Clonando..."
  cd /mnt/seagate/repos
  git clone https://github.com/juliocadenas/IA-HUB-MADRID1.git
  cd IA-HUB-MADRID1
}
git pull origin main || echo "⚠️  Git pull falló, continuando..."
echo "✅ Repo actualizado"

echo ""
echo "=== [3/8] DEPLOY CONFIG.PY DEL GATEWAY ==="
GATEWAY_PATH="/mnt/seagate/api/ai-hub-gateway"
if [ -d "$GATEWAY_PATH/gateway" ]; then
  cp gateway/config.py "$GATEWAY_PATH/gateway/config.py"
  echo "✅ config.py copiado al Gateway"
else
  echo "⚠️  $GATEWAY_PATH no existe. ¿El Gateway está en otro lado?"
  echo "  Buscando..."
  GATEWAY_PATH=$(find / -name "config.py" -path "*/gateway/*" 2>/dev/null | head -1 | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null)
  if [ -n "$GATEWAY_PATH" ]; then
    echo "  Encontrado en: $GATEWAY_PATH"
    cp gateway/config.py "$GATEWAY_PATH/gateway/config.py"
    echo "✅ config.py copiado"
  else
    echo "❌ No se encontró el Gateway. Saltando..."
  fi
fi

echo ""
echo "=== [4/8] MOVER OLLAMA AL SEAGATE ==="
OLLAMA_CURRENT="/usr/share/ollama/.ollama/models"
OLLAMA_TARGET="/mnt/seagate/models/llm/ollama"

if [ -d "$OLLAMA_CURRENT" ]; then
  OLLAMA_SIZE=$(du -sh "$OLLAMA_CURRENT" 2>/dev/null | awk '{print $1}')
  echo "  Modelos actuales en disco principal: ${OLLAMA_SIZE}"
  
  echo "  Deteniendo Ollama..."
  systemctl stop ollama
  
  mkdir -p "$OLLAMA_TARGET"
  
  echo "  Copiando modelos al Seagate (puede tardar)..."
  rsync -av --progress "$OLLAMA_CURRENT/" "$OLLAMA_TARGET/"
  
  echo "  Configurando OLLAMA_MODELS..."
  mkdir -p /etc/systemd/system/ollama.service.d
  cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_MODELS=/mnt/seagate/models/llm/ollama"
EOF
  
  echo "  Iniciando Ollama..."
  systemctl daemon-reload
  systemctl start ollama
  
  # Verificar
  sleep 3
  if systemctl is-active --quiet ollama; then
    echo "✅ Ollama migrado al Seagate y funcionando"
    # Borrar viejo (descomentar cuando se verifique que funciona)
    # rm -rf "$OLLAMA_CURRENT"
    echo "  ℹ️  Modelos viejos en $OLLAMA_CURRENT (borrar manualmente cuando confirmes)"
  else
    echo "❌ Ollama no arrancó. Revirtiendo..."
    rm /etc/systemd/system/ollama.service.d/override.conf
    systemctl daemon-reload
    systemctl start ollama
  fi
else
  echo "  ℹ️  No hay modelos en disco principal. Verificando configuración..."
  if grep -q "/mnt/seagate" /etc/systemd/system/ollama.service.d/override.conf 2>/dev/null; then
    echo "✅ Ollama ya configurado para Seagate"
  else
    echo "⚠️  Creando configuración para Seagate..."
    mkdir -p /etc/systemd/system/ollama.service.d
    cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_MODELS=/mnt/seagate/models/llm/ollama"
EOF
    systemctl daemon-reload
    systemctl restart ollama
  fi
fi

echo ""
echo "=== [5/8] INSTALAR WATCHDOGS PCIe ==="
# PCIe watchdog
cp scripts/pcie-watchdog.sh /usr/local/bin/
chmod +x /usr/local/bin/pcie-watchdog.sh
cp scripts/pcie-watchdog.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now pcie-watchdog 2>/dev/null || true
echo "✅ PCIe watchdog instalado"

# VRAM watchdog
cp scripts/vram-watchdog.sh /usr/local/bin/ 2>/dev/null || true
chmod +x /usr/local/bin/vram-watchdog.sh 2>/dev/null || true
cp scripts/vram-watchdog.service /etc/systemd/system/ 2>/dev/null || true
systemctl daemon-reload
systemctl enable --now vram-watchdog 2>/dev/null || true
echo "✅ VRAM watchdog instalado"

echo ""
echo "=== [6/8] INITRAMFS HARDENING ==="
# Auto-fsck script
cp scripts/initramfs-auto-fsck.sh /etc/initramfs-tools/scripts/init-premount/zz-auto-fsck 2>/dev/null || true
chmod +x /etc/initramfs-tools/scripts/init-premount/zz-auto-fsck 2>/dev/null || true

# Panic guard
cp scripts/initramfs-panic-guard.sh /etc/initramfs-tools/scripts/init-bottom/zz-panic-guard 2>/dev/null || true
chmod +x /etc/initramfs-tools/scripts/init-bottom/zz-panic-guard 2>/dev/null || true

# Sysctl
cp scripts/99-panic-reboot.conf /etc/sysctl.d/99-panic-reboot.conf 2>/dev/null || true
sysctl --system 2>/dev/null || true

# tune2fs - fsck cada boot
tune2fs -c 1 /dev/sda3 2>/dev/null || echo "  ⚠️  No se pudo aplicar tune2fs (¿partición diferente?)"

# Reconstruir initramfs
echo "  Reconstruyendo initramfs (puede tardar 1-2 min)..."
update-initramfs -u -k all 2>/dev/null || echo "  ⚠️  update-initramfs falló"
echo "✅ Initramfs hardening aplicado"

echo ""
echo "=== [7/8] OOM PROTECTION ==="
mkdir -p /etc/systemd/system/ollama.service.d /etc/systemd/system/ai-hub-gateway.service.d
cp scripts/oom-protection-dropins.conf /etc/systemd/system/ollama.service.d/oom.conf 2>/dev/null || true
cp scripts/oom-protection-dropins.conf /etc/systemd/system/ai-hub-gateway.service.d/oom.conf 2>/dev/null || true
systemctl daemon-reload
echo "✅ OOM protection aplicado"

echo ""
echo "=== [8/9] DEPLOY SERVICIOS DOCKER ==="
if [ -d "$GATEWAY_PATH" ]; then
  echo "  Copiando docker-compose.yml..."
  cp ai-hub-gateway/docker-compose.yml "$GATEWAY_PATH/"

  echo "  Copiando servicios Docker..."
  mkdir -p "$GATEWAY_PATH/services"
  cp -r ai-hub-gateway/services/* "$GATEWAY_PATH/services/" 2>/dev/null || true

  echo "  Copiando routers actualizados..."
  cp ai-hub-gateway/gateway/routers/voice.py "$GATEWAY_PATH/gateway/routers/" 2>/dev/null || true
  cp ai-hub-gateway/gateway/routers/effects.py "$GATEWAY_PATH/gateway/routers/" 2>/dev/null || true

  echo "✅ Servicios Docker copiados al Gateway"
  echo "  Para activar: cd $GATEWAY_PATH && docker compose --profile voice up -d"
else
  echo "⚠️  No se encontro el Gateway. Saltando deploy Docker."
fi

echo ""
echo "=== [9/9] REINICIAR GATEWAY ==="
systemctl restart ai-hub-gateway
sleep 5
if systemctl is-active --quiet ai-hub-gateway; then
  echo "✅ Gateway reiniciado y funcionando"
else
  echo "❌ Gateway no arrancó. Revisar: journalctl -u ai-hub-gateway -f"
fi

echo ""
echo "================================================"
echo "  ✅ DEPLOY COMPLETADO!"
echo "================================================"
echo ""
echo "=== ESTADO FINAL ==="
echo "--- GPU ---"
nvidia-smi --query-gpu=temperature.gpu,memory.used,memory.total --format=csv,noheader
echo "--- Disco ---"
df -h / /mnt/seagate
echo "--- Servicios ---"
systemctl is-active ai-hub-gateway ollama pcie-watchdog vram-watchdog
echo "--- Gateway Status ---"
curl -s http://localhost:9000/v1/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"]}'); print(f'Servicios online: {len([s for s in d[\"services\"] if s[\"status\"]==\"online\"])}/{len(d[\"services\"])}')" 2>/dev/null || echo "No se pudo obtener status"
echo ""
echo "================================================"
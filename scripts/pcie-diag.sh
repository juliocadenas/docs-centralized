#!/bin/bash
# Diagnóstico completo PCIe + GPU para NAB9
# Ejecutar como root: sudo bash pcie-diag.sh
# 
# Diagnostica: errores PCIe, estado GPU, temps, alimentación, slot

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
hdr()  { echo -e "\n${YELLOW}═══ $1 ═══${NC}"; }

hdr "1. ESTADO DE LA GPU"
if command -v nvidia-smi &>/dev/null; then
    if timeout 10 nvidia-smi; then
        ok "nvidia-smi responde correctamente"
    else
        fail "nvidia-smi NO responde - GPU colgada"
        warn "Intentando reset..."
        modprobe -r nvidia_uvm nvidia_drm nvidia_modeset nvidia 2>/dev/null
        sleep 2
        modprobe nvidia nvidia_modeset nvidia_drm nvidia_uvm 2>/dev/null
        sleep 3
        if timeout 10 nvidia-smi; then
            ok "GPU recuperada tras reset de módulo"
        else
            fail "GPU sigue sin responder - REINICIO RECOMENDADO"
        fi
    fi
else
    fail "nvidia-smi no instalado o no en PATH"
fi

hdr "2. ERRORES PCIe EN DMESG (últimas 24h)"
PCIE_ERRS=$(dmesg --time-format=iso 2>/dev/null | grep -c "PCIe Bus Error" || echo 0)
echo "Total errores PCIe: $PCIE_ERRS"
if [ "$PCIE_ERRS" -gt 50 ]; then
    fail "Demasiados errores PCIe ($PCIE_ERRS) - problema de hardware"
    echo "Últimos 10 errores:"
    dmesg | grep "PCIe Bus Error" | tail -10
elif [ "$PCIE_ERRS" -gt 0 ]; then
    warn "Algunos errores PCIe ($PCIE_ERRS) - vigilar"
else
    ok "Sin errores PCIe"
fi

hdr "3. INFO PCIe DE LA GPU"
echo "Dispositivos NVIDIA en bus PCIe:"
lspci | grep -i nvidia
echo ""
echo "Detalle del slot PCIe:"
lspci -vvv -s $(lspci | grep -i nvidia | head -1 | awk '{print $1}') 2>/dev/null | grep -E "(LnkSta|LnkCap|Width|Speed)" || warn "No se pudo obtener info PCIe"

hdr "4. TEMPERATURAS GPU"
if timeout 10 nvidia-smi --query-gpu=temperature.gpu,power.draw,power.limit,clocks.gr,clocks.mem --format=csv 2>/dev/null; then
    ok "Datos de GPU obtenidos"
else
    fail "No se pudieron obtener métricas de GPU"
fi

hdr "5. ALIMENTACIÓN GPU"
echo "Sensores de potencia (si disponibles):"
sensors 2>/dev/null | grep -iE "(power|12v|gpu)" || echo "lm-sensors no disponible o sin datos"

hdr "6. SERVICIOS AI HUB"
for svc in ai-hub-gateway ollama; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        ok "$svc: activo"
    else
        fail "$svc: inactivo"
    fi
done

hdr "7. PROCESOS GPU"
if timeout 10 nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv 2>/dev/null; then
    ok "Procesos listados"
else
    warn "No hay procesos GPU o GPU no responde"
fi

hdr "8. ESPACIO EN DISCO"
df -h /mnt/seagate / 2>/dev/null | grep -v tmpfs

hdr "9. MEMORIA RAM"
free -h

hdr "10. RECOMENDACIONES"
if [ "$PCIE_ERRS" -gt 100 ]; then
    echo -e "${RED}══════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ⚠️  ACCIÓN REQUERIDA:${NC}"
    echo -e "${RED}  1. Apagar servidor: sudo shutdown now${NC}"
    echo -e "${RED}  2. Abrir chasis y revisar:${NC}"
    echo -e "${RED}     - GPU bien sentada en slot PCIe${NC}"
    echo -e "${RED}     - Cables de alimentación GPU firmes${NC}"
    echo -e "${RED}     - Riser PCIe (si usa) - considerar reemplazar${NC}"
    echo -e "${RED}  3. En BIOS: fijar PCIe Gen a Gen4 (no Auto)${NC}"
    echo -e "${RED}  4. Encender y monitorear dmesg:${NC}"
    echo -e "${RED}     sudo dmesg -w | grep -i 'pcie\\|nvidia'${NC}"
    echo -e "${RED}══════════════════════════════════════════════════${NC}"
else
    ok "Sistema estable - instalar watchdog para prevenir futuros cuelgues"
    echo "  sudo cp scripts/pcie-watchdog.sh /usr/local/bin/"
    echo "  sudo cp scripts/pcie-watchdog.service /etc/systemd/system/"
    echo "  sudo systemctl enable --now pcie-watchdog"
fi

echo ""
echo "Diagnóstico completado: $(date)"
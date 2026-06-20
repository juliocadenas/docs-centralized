#!/bin/bash
# Diagnóstico específico para NAB9 (Minisforum + OCuLink + Docker Base DG2)
# Ejecutar como root: sudo bash pcie-diag.sh
#
# ARQUITECTURA NAB9:
# - PC: Minisforum (mini PC, cabe en la mano)
# - GPU: RTX 5080 16GB (en Docker Base DG2 externa)
# - CONEXIÓN: OCuLink (M.2+Key → cable OCuLink → Docker Base DG2)
# - SIN slots PCIe adicionales, solo USB3/USB4
#
# CAUSAS COMUNES de errores PCIe en este setup:
# 1. Cable OCuLink flojo o mal conectado
# 2. Cable OCuLink de mala calidad o dañado
# 3. Docker Base DG2 sobrecalentándose
# 4. Negociación PCIe Gen incorrecta (Auto falla con OCuLink)
# 5. Firmware Docker Base DG2 desactualizado

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
hdr()  { echo -e "\n${CYAN}═══ $1 ═══${NC}"; }

hdr "1. ESTADO DE LA GPU (RTX 5080 vía OCuLink)"
if command -v nvidia-smi &>/dev/null; then
    if timeout 10 nvidia-smi; then
        ok "nvidia-smi responde - GPU accesible vía OCuLink"
    else
        fail "nvidia-smi NO responde - GPU inaccesible"
        warn "CAUSAS POSIBLES:"
        echo "  → Cable OCuLink desconectado o flojo"
        echo "  → Docker Base DG2 apagada o sin energía"
        echo "  → OCuLink negotiation falló en boot"
        echo ""
        warn "Verificando conexión OCuLink..."
        lspci | grep -i nvidia && ok "GPU detectada en bus PCIe" || fail "GPU NO detectada - OCuLink desconectado"
    fi
else
    fail "nvidia-smi no instalado"
fi

hdr "2. ERRORES PCIe (INDICADOR DE PROBLEMA OCULINK)"
PCIE_ERRS=$(dmesg --time-format=iso 2>/dev/null | grep -c "PCIe Bus Error" || echo 0)
echo "Total errores PCIe desde boot: $PCIE_ERRS"
if [ "$PCIE_ERRS" -gt 100 ]; then
    fail "ERRORES CRÍTICOS ($PCIE_ERRS) - Problema de CONEXIÓN OCuLink"
    echo ""
    echo "Últimos errores:"
    dmesg | grep "PCIe Bus Error" | tail -5
    echo ""
    warn "Solución más probable:"
    echo "  1. Apagar Minisforum: sudo shutdown now"
    echo "  2. Desconectar cable OCuLink de AMBOS extremos"
    echo "  3. Reconectar firmemente (escuchar 'click')"
    echo "  4. Verificar que Docker Base DG2 tenga luz verde"
    echo "  5. Encender Minisforum"
elif [ "$PCIE_ERRS" -gt 10 ]; then
    warn "Errores PCIe moderados ($PCIE_ERRS) - Vigilar cable OCuLink"
else
    ok "Pocos errores PCIe ($PCIE_ERRS) - OCuLink estable"
fi

hdr "3. NEGOCIACIÓN PCIe GEN (CRÍTICO PARA OCULINK)"
echo "GPU en bus PCIe:"
lspci | grep -i nvidia
echo ""
echo "Capacidad y Estado del enlace PCIe:"
GPU_ADDR=$(lspci | grep -i nvidia | head -1 | awk '{print $1}')
if [ -n "$GPU_ADDR" ]; then
    echo "(LnkCap = max soportado, LnkSta = actual)"
    lspci -vvv -s "$GPU_ADDR" 2>/dev/null | grep -E "(LnkCap|LnkSta)" | head -4
    echo ""
    # Extraer velocidades
    CUR_SPEED=$(lspci -vvv -s "$GPU_ADDR" 2>/dev/null | grep "LnkSta:" | grep -oP "Speed \K[0-9.]+GT/s")
    MAX_SPEED=$(lspci -vvv -s "$GPU_ADDR" 2>/dev/null | grep "LnkCap:" | grep -oP "Speed \K[0-9.]+GT/s")
    CUR_WIDTH=$(lspci -vvv -s "$GPU_ADDR" 2>/dev/null | grep "LnkSta:" | grep -oP "Width x\K[0-9]+")
    MAX_WIDTH=$(lspci -vvv -s "$GPU_ADDR" 2>/dev/null | grep "LnkCap:" | grep -oP "Width x\K[0-9]+")
    
    echo "Velocidad actual: ${CUR_SPEED:-?} GT/s (máx: ${MAX_SPEED:-?} GT/s)"
    echo "Ancho actual:     x${CUR_WIDTH:-?} (máx: x${MAX_WIDTH:-?})"
    
    if [ -n "$CUR_SPEED" ] && [ -n "$MAX_SPEED" ]; then
        if (( $(echo "$CUR_SPEED < $MAX_SPEED" | bc -l 2>/dev/null || echo 0) )); then
            fail "GPU NO está a velocidad máxima (${CUR_SPEED} vs ${MAX_SPEED} GT/s)"
            warn "CAUSA: OCuLink limita el enlace o PCIe Gen mal configurado"
            echo "  → En BIOS Minisforum: fijar PCIe Gen (probar Gen4 o Gen3)"
            echo "  → OCuLink típicamente soporta Gen4 x4 (≈8GB/s)"
        else
            ok "GPU a velocidad máxima (${CUR_SPEED} GT/s)"
        fi
    fi
else
    fail "GPU no detectada en bus PCIe"
fi

hdr "4. TEMPERATURA Y POTENCIA GPU"
if timeout 10 nvidia-smi --query-gpu=temperature.gpu,power.draw,power.limit,clocks.gr,clocks.mem,pcie.link.gen.current,pcie.link.width.current --format=csv 2>/dev/null; then
    ok "Métricas obtenidas"
    echo ""
    TEMP=$(timeout 10 nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null)
    if [ -n "$TEMP" ] && [ "$TEMP" -gt 85 ]; then
        fail "GPU MUY CALIENTE (${TEMP}°C) - Revisar ventilación Docker Base DG2"
    elif [ -n "$TEMP" ] && [ "$TEMP" -gt 75 ]; then
        warn "GPU caliente (${TEMP}°C) - Monitorear"
    fi
else
    fail "No se pudieron obtener métricas - GPU inaccesible"
fi

hdr "5. ESTADO DOCKER BASE DG2"
echo "Bus PCIe con dispositivos externos:"
lspci | grep -iE "(display|3d|vga)" || warn "No hay GPU detectada"
echo ""
echo "Verificando si OCuLink está activo:"
if lspci | grep -qi nvidia; then
    ok "OCuLink ACTIVO - GPU detectada en bus"
else
    fail "OCuLink INACTIVO - GPU no detectada"
    echo "  → Revisar cable OCuLink físicamente"
    echo "  → Verificar Docker Base DG2 encendida"
fi

hdr "6. SERVICIOS AI HUB"
for svc in ai-hub-gateway ollama; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        ok "$svc: activo"
    else
        fail "$svc: inactivo"
    fi
done

hdr "7. MEMORIA Y DISCO"
free -h | grep -E "(Mem|Swap)"
echo ""
df -h /mnt/seagate / 2>/dev/null | grep -v tmpfs

hdr "8. RECOMENDACIONES ESPECÍFICAS OCuLink"
if [ "$PCIE_ERRS" -gt 100 ]; then
    echo -e "${RED}══════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  🚨 PROBLEMA OCuLink DETECTADO (${PCIE_ERRS} errores)${NC}"
    echo -e "${RED}══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}  SOLUCIÓN PASO A PASO:${NC}"
    echo ""
    echo "  1. Apagar Minisforum:"
    echo "     sudo shutdown now"
    echo ""
    echo "  2. Desconectar cable OCuLink:"
    echo "     - Del Minisforum (M.2+Key)"
    echo "     - De la Docker Base DG2"
    echo ""
    echo "  3. Inspeccionar cable OCuLink:"
    echo "     - ¿Pines doblados/dañados? → reemplazar cable"
    echo "     - ¿Cable demasiado largo? (>30cm causa errores)"
    echo "     - ¿Cable de buena calidad? (mejor marca: LinkUp, MODDIY)"
    echo ""
    echo "  4. Reconectar firmemente (escuchar 'click' ambos lados)"
    echo ""
    echo "  5. Verificar Docker Base DG2:"
    echo "     - Luz de energía encendida"
    echo "     - Ventiladores girando"
    echo "     - Conexión de poder firme"
    echo ""
    echo "  6. Encender Minisforum y monitorear:"
    echo "     sudo dmesg -w | grep -iE 'pcie|nvidia'"
    echo ""
    echo "  7. Si persiste, en BIOS fijar PCIe a Gen4 (no Auto)"
    echo ""
    echo -e "${RED}══════════════════════════════════════════════════════${NC}"
else
    ok "OCuLink funcionando - instalar watchdog preventivo"
    echo "  sudo cp scripts/pcie-watchdog.sh /usr/local/bin/"
    echo "  sudo cp scripts/pcie-watchdog.service /etc/systemd/system/"
    echo "  sudo systemctl enable --now pcie-watchdog"
fi

echo ""
echo "Diagnóstico completado: $(date)"
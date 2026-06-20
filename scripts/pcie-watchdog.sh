#!/bin/bash
# PCIe/GPU Watchdog para NAB9 (Minisforum + OCuLink + Docker Base DG2)
# 
# ARQUITECTURA: RTX 5080 conectada vía OCuLink (M.2+Key) a Docker Base DG2
# El OCuLink es sensible a vibraciones, temperatura y calidad del cable.
# Este watchdog detecta degradación del enlace y reinicia antes de un cuelgue total.
#
# Instalar:
#   sudo cp pcie-watchdog.sh /usr/local/bin/
#   sudo chmod +x /usr/local/bin/pcie-watchdog.sh
#   sudo cp pcie-watchdog.service /etc/systemd/system/
#   sudo systemctl enable --now pcie-watchdog

LOG="/var/log/pcie-watchdog.log"
THRESHOLD=50        # Errores PCIe/min antes de actuar (OCuLink es más sensible)
CHECK_INTERVAL=20   # Segundos entre checks
MAX_RECOVERIES=3    # Max recuperación suave antes de reboot forzado

# Contador de recuperaciones (se resetea tras 1h estable)
RECOVERY_COUNT=0
LAST_RECOVERY=0

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
    logger -t pcie-watchdog "$1"
}

count_pcie_errors_recent() {
    # Cuenta errores PCIe en el último minuto
    journalctl -k --since "1 min ago" --no-pager 2>/dev/null | grep -c "PCIe Bus Error" || echo 0
}

check_gpu_alive() {
    timeout 8 nvidia-smi >/dev/null 2>&1
    return $?
}

check_oculink_active() {
    # Verifica que la GPU sigue detectada en el bus PCIe
    lspci 2>/dev/null | grep -qi nvidia
    return $?
}

recover_gpu_soft() {
    log "⚠️  Intentando recuperación suave (intentos: $RECOVERY_COUNT)..."
    
    # 1. Matar procesos GPU
    log "  - Deteniendo procesos GPU..."
    systemctl stop ai-hub-gateway 2>/dev/null
    pkill -9 -f "ollama" 2>/dev/null
    pkill -9 -f "comfyui" 2>/dev/null
    pkill -9 -f "wan2gp" 2>/dev/null
    pkill -9 -f "documusic" 2>/dev/null
    pkill -9 -f "python.*main.py" 2>/dev/null
    
    sleep 3
    
    # 2. Intentar recargar módulo nvidia
    log "  - Recargando módulos nvidia..."
    modprobe -r nvidia_uvm nvidia_drm nvidia_modeset nvidia 2>/dev/null
    sleep 2
    modprobe nvidia nvidia_modeset nvidia_drm nvidia_uvm 2>/dev/null
    sleep 5
    
    # 3. Verificar
    if check_gpu_alive && check_oculink_active; then
        log "✅ GPU recuperada tras recarga de módulo"
        systemctl start ai-hub-gateway 2>/dev/null
        RECOVERY_COUNT=$((RECOVERY_COUNT + 1))
        LAST_RECOVERY=$(date +%s)
        return 0
    fi
    
    log "❌ Recuperación suave falló"
    RECOVERY_COUNT=$((RECOVERY_COUNT + 1))
    LAST_RECOVERY=$(date +%s)
    return 1
}

emergency_reboot() {
    log "🚨 REBOOT DE EMERENCIA - OCuLink/GPU no recuperable"
    log "   Esto indica problema físico: cable OCuLink, Docker Base DG2, o GPU"
    
    # Notificar vía Telegram si está configurado
    if [ -f /usr/local/bin/telegram-alert ]; then
        /usr/local/bin/telegram-alert "🚨 NAB9 REBOOT DE EMERENCIA
Errores PCIe críticos en OCuLink.
Revisar: cable OCuLink, Docker Base DG2, alimentación GPU." 2>/dev/null &
    fi
    
    sleep 5
    sync; sync; sync
    echo b > /proc/sysrq-trigger 2>/dev/null || reboot -f
}

# === MAIN ===
log "🚀 PCIe/OCuLink Watchdog iniciado"
log "   Threshold: $THRESHOLD errores/min | Interval: ${CHECK_INTERVAL}s | Max recoveries: $MAX_RECOVERIES"

while true; do
    # Reset contador si lleva 1h estable
    NOW=$(date +%s)
    if [ $RECOVERY_COUNT -gt 0 ] && [ $((NOW - LAST_RECOVERY)) -gt 3600 ]; then
        log "📊 Sistema estable 1h - reseteando contador de recuperaciones"
        RECOVERY_COUNT=0
    fi
    
    pcie_errs=$(count_pcie_errors_recent)
    gpu_ok="FAIL"
    check_gpu_alive && gpu_ok="OK"
    oculink_ok="FAIL"
    check_oculink_active && oculink_ok="OK"
    
    # Log estado cada 5 min
    if [ $((NOW % 300)) -lt $CHECK_INTERVAL ]; then
        log "📊 Estado: PCIe_errs=${pcie_errs}/min, GPU=${gpu_ok}, OCuLink=${oculink_ok}, recoveries=${RECOVERY_COUNT}/${MAX_RECOVERIES}"
    fi
    
    NEEDS_RECOVERY=false
    REASON=""
    
    # Condición 1: Errores PCIe masivos
    if [ "$pcie_errs" -gt "$THRESHOLD" ]; then
        NEEDS_RECOVERY=true
        REASON="${pcie_errs} errores PCIe/min (OCuLink degradado)"
    fi
    
    # Condición 2: GPU no responde
    if [ "$gpu_ok" = "FAIL" ]; then
        NEEDS_RECOVERY=true
        REASON="nvidia-smi no responde"
    fi
    
    # Condición 3: OCuLink desconectado
    if [ "$oculink_ok" = "FAIL" ]; then
        log "🚨 CRÍTICO: GPU no detectada en bus PCIe - OCuLink DESCONECTADO"
        log "   Probablemente cable físico desconectado o Docker Base DG2 apagada"
        emergency_reboot
        exit 1
    fi
    
    if [ "$NEEDS_RECOVERY" = "true" ]; then
        log "🚨 CRÍTICO: $REASON"
        
        if [ $RECOVERY_COUNT -ge $MAX_RECOVERIES ]; then
            log "❌ Máximo de recuperaciones alcanzado ($MAX_RECOVERIES)"
            emergency_reboot
            exit 1
        fi
        
        recover_gpu_soft
        sleep 30  # Esperar tras recuperación
        continue
    fi
    
    sleep $CHECK_INTERVAL
done
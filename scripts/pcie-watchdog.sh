#!/bin/bash
# PCIe/GPU Watchdog - Detecta errores PCIe y reinicia el sistema
# Instalar: sudo cp pcie-watchdog.sh /usr/local/bin/
#           sudo chown root:root /usr/local/bin/pcie-watchdog.sh
#           sudo chmod +x /usr/local/bin/pcie-watchdog.sh
#
# Systemd: cp pcie-watchdog.service /etc/systemd/system/
#          sudo systemctl enable --now pcie-watchdog

LOG="/var/log/pcie-watchdog.log"
THRESHOLD=100  # Máximo de errores PCIe antes de actuar
CHECK_INTERVAL=30  # Segundos entre checks

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
    logger -t pcie-watchdog "$1"
}

count_pcie_errors() {
    # Cuenta errores PCIe correctables en el último minuto
    dmesg --time-format=iso 2>/dev/null | \
    awk -v cutoff="$(date -d '1 min ago' '+%Y-%m-%dT%H:%M' 2>/dev/null || date -v-1M '+%Y-%m-%dT%H:%M')" \
    '$1 >= cutoff' | \
    grep -c "PCIe Bus Error" 2>/dev/null || echo 0
}

check_gpu_alive() {
    # Verifica que nvidia-smi responde
    timeout 10 nvidia-smi >/dev/null 2>&1
    return $?
}

check_nvidia_errors() {
    # Verifica errores de nvidia-modeset
    dmesg --time-format=iso 2>/dev/null | \
    awk -v cutoff="$(date -d '1 min ago' '+%Y-%m-%dT%H:%M' 2>/dev/null || date -v-1M '+%Y-%m-%dT%H:%M')" \
    '$1 >= cutoff' | \
    grep -c "nvidia-modeset.*ERROR" 2>/dev/null || echo 0
}

recover_gpu() {
    log "⚠️  Intentando recuperación suave de GPU..."
    
    # Intentar reset de módulo nvidia
    log "  - Deteniendo servicios GPU..."
    systemctl stop ai-hub-gateway 2>/dev/null
    pkill -9 -f "ollama" 2>/dev/null
    pkill -9 -f "comfyui" 2>/dev/null
    pkill -9 -f "wan2gp" 2>/dev/null
    pkill -9 -f "documusic" 2>/dev/null
    
    sleep 5
    
    # Intentar recargar módulo nvidia
    log "  - Recargando módulo nvidia..."
    modprobe -r nvidia_uvm nvidia_drm nvidia_modeset nvidia 2>/dev/null
    sleep 2
    modprobe nvidia nvidia_modeset nvidia_drm nvidia_uvm 2>/dev/null
    sleep 5
    
    if check_gpu_alive; then
        log "✅ GPU recuperada tras recarga de módulo"
        systemctl start ai-hub-gateway 2>/dev/null
        return 0
    fi
    
    log "❌ Recuperación suave falló. Reiniciando sistema en 10s..."
    sleep 10
    
    # Forzar sync antes del reboot
    sync
    sync
    sync
    
    # Reboot de emergencia
    echo b > /proc/sysrq-trigger 2>/dev/null || reboot -f
    return 1
}

# === MAIN LOOP ===
log "🚀 PCIe Watchdog iniciado (threshold=$THRESHOLD errores, interval=${CHECK_INTERVAL}s)"

while true; do
    pcie_errs=$(count_pcie_errors)
    nvidia_errs=$(check_nvidia_errors)
    gpu_ok=$(check_gpu_alive && echo "OK" || echo "FAIL")
    
    # Log cada minuto (2 ciclos)
    if [ $((SECONDS % 60)) -lt $CHECK_INTERVAL ]; then
        log "Estado: PCIe_errs=${pcie_errs}/min, NV_errs=${nvidia_errs}/min, GPU=${gpu_ok}"
    fi
    
    # Condición 1: Demasiados errores PCIe
    if [ "$pcie_errs" -gt "$THRESHOLD" ]; then
        log "🚨 CRÍTICO: ${pcie_errs} errores PCIe en 1 min (threshold: ${THRESHOLD})"
        recover_gpu
        sleep 60  # Esperar antes de volver a checkear
        continue
    fi
    
    # Condición 2: GPU no responde
    if [ "$gpu_ok" = "FAIL" ]; then
        log "🚨 CRÍTICO: nvidia-smi no responde"
        recover_gpu
        sleep 60
        continue
    fi
    
    # Condición 3: Errores de nvidia-modeset
    if [ "$nvidia_errs" -gt 5 ]; then
        log "🚨 CRÍTICO: ${nvidia_errs} errores nvidia-modeset en 1 min"
        recover_gpu
        sleep 60
        continue
    fi
    
    sleep $CHECK_INTERVAL
done
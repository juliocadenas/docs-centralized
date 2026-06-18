#!/bin/bash
# ============================================================================
# vram-watchdog.sh - OS-level VRAM + NVIDIA driver watchdog
# ============================================================================
# Monitors GPU health at the OS level, INDEPENDENT of any application.
#
# Three levels of protection:
#   1. VRAM OOM prevention (kill processes before OOM crash)
#   2. NVIDIA driver crash detection (reload modules if driver hangs)
#   3. Emergency clean reboot (sync before reboot to prevent corruption)
#
# Install: /usr/local/bin/vram-watchdog.sh
# Service: /etc/systemd/system/vram-watchdog.service
# Log: /var/log/vram-watchdog.log
# ============================================================================

set -u

# ============================================================================
# Configuration
# ============================================================================
CHECK_INTERVAL=10              # Seconds between checks
WARN_THRESHOLD_PCT=85          # Warn at this VRAM usage
SOFT_KILL_THRESHOLD_PCT=90     # Kill non-essential GPU procs
HARD_KILL_THRESHOLD_PCT=95     # Kill ALL GPU procs except protected
CRITICAL_REBOOT_PCT=98         # If VRAM still maxed after kills, reboot clean

# NVIDIA driver crash detection
NVIDIA_SMI_FAIL_THRESHOLD=6    # Consecutive nvidia-smi failures before driver reload
NVIDIA_RELOAD_FAIL_THRESHOLD=3 # Driver reload failures before emergency reboot

# Services that should NEVER be killed (protected)
PROTECTED_PATTERNS=(
    "ollama"
    "Xorg"
    "gnome-shell"
    "vram-watchdog"
)

# Non-essential GPU services (safe to kill/restart)
NON_ESSENTIAL_PATTERNS=(
    "python.*comfyui"
    "python.*wan2gp"
    "python.*documusic"
    "python.*musetalk"
    "python.*latentsync"
    "python.*liveportrait"
    "python.*hallo2"
    "python.*serve_avatar"
    "python.*effects_svc"
    "python.*cogvideox"
    "python.*storydiffusion"
    "python.*real_esrgan"
    "python.*esrgan"
    "python.*whisper"
    "python.*piper"
    "comfyui"
    "wan2gp"
    "whisper"
    "piper"
)

# All AI services for emergency shutdown
ALL_AI_SERVICES=(
    "ai-hub-gateway" "comfyui" "wan2gp" "documusic"
    "musetalk" "latentsync" "liveportrait" "hallo2"
    "effects" "ai-hub-effects" "effects_services"
    "avatar" "avatar_services" "tts" "stt"
)

LOG="/var/log/vram-watchdog.log"

# ============================================================================
# Functions
# ============================================================================

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log() {
    echo "$(timestamp) [VRAM-WATCHDOG] $*" | tee -a "$LOG"
}

is_protected() {
    local proc_name="$1"
    for pattern in "${PROTECTED_PATTERNS[@]}"; do
        if echo "$proc_name" | grep -qiE "$pattern"; then
            return 0
        fi
    done
    return 1
}

is_non_essential() {
    local proc_name="$1"
    for pattern in "${NON_ESSENTIAL_PATTERNS[@]}"; do
        if echo "$proc_name" | grep -qiE "$pattern"; then
            return 0
        fi
    done
    return 1
}

get_vram_info() {
    # Returns: "used_mb free_mb total_mb utilization_pct"
    # Returns empty string if nvidia-smi fails
    nvidia-smi --query-gpu=memory.used,memory.free,memory.total,utilization.gpu \
        --format=csv,noheader,nounits 2>/dev/null | awk -F', ' '{print $1, $2, $3, $4}'
}

get_gpu_processes() {
    nvidia-smi --query-compute-apps=pid,used_memory,process_name \
        --format=csv,noheader,nounits 2>/dev/null
}

kill_process_gracefully() {
    local pid="$1"
    local name="$2"

    log "  -> Killing PID $pid ($name) [SIGTERM]..."
    kill -TERM "$pid" 2>/dev/null || true

    local waited=0
    while [ "$waited" -lt 5 ]; do
        if ! kill -0 "$pid" 2>/dev/null; then
            log "  OK: PID $pid terminated gracefully"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done

    log "  -> PID $pid didn't respond, force killing [SIGKILL]..."
    kill -9 "$pid" 2>/dev/null || true
    sleep 1

    if ! kill -0 "$pid" 2>/dev/null; then
        log "  OK: PID $pid killed"
    else
        log "  FAIL: Could not kill PID $pid!"
    fi
}

soft_kill_non_essential() {
    log "SOFT KILL: Stopping non-essential GPU processes..."
    local killed=0

    # Stop systemd services first (cleaner)
    for svc in comfyui wan2gp documusic musetalk latentsync liveportrait hallo2 effects ai-hub-effects; do
        if systemctl is-active --quiet "$svc" 2>/dev/null; then
            log "  -> Stopping service: $svc"
            systemctl stop "$svc" 2>/dev/null || true
        fi
    done

    sleep 2

    # Kill remaining non-essential GPU processes
    while read -r pid vram_mb proc_name; do
        [ -z "$pid" ] && continue
        proc_name_trimmed=$(echo "$proc_name" | xargs)

        if is_protected "$proc_name_trimmed"; then
            log "  SKIP PROTECTED: PID $pid ($proc_name_trimmed) ${vram_mb}MB"
            continue
        fi

        if is_non_essential "$proc_name_trimmed"; then
            kill_process_gracefully "$pid" "$proc_name_trimmed"
            killed=$((killed + 1))
        fi
    done < <(get_gpu_processes)

    log "SOFT KILL complete: $killed killed"
    sleep 3
}

hard_kill_all_non_protected() {
    log "HARD KILL: Killing ALL non-protected GPU processes (emergency)..."
    local killed=0

    # Stop ALL services forcefully
    for svc in "${ALL_AI_SERVICES[@]}"; do
        systemctl stop "$svc" 2>/dev/null || true
    done

    sleep 2

    # Kill every GPU process that's not protected
    while read -r pid vram_mb proc_name; do
        [ -z "$pid" ] && continue
        proc_name_trimmed=$(echo "$proc_name" | xargs)

        if is_protected "$proc_name_trimmed"; then
            log "  SKIP PROTECTED: PID $pid ($proc_name_trimmed)"
            continue
        fi

        kill_process_gracefully "$pid" "$proc_name_trimmed"
        killed=$((killed + 1))
    done < <(get_gpu_processes)

    # Kill rogue python processes using GPU
    while read -r pid; do
        [ -z "$pid" ] && continue
        local cmd
        cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
        if echo "$cmd" | grep -qiE "torch|cuda|comfy|wan2|music|avatar|esrgan|whisper|piper"; then
            log "  -> Killing rogue GPU python: PID $pid"
            kill -9 "$pid" 2>/dev/null || true
            killed=$((killed + 1))
        fi
    done < <(pgrep -f python 2>/dev/null)

    log "HARD KILL complete: $killed killed"
    sleep 5
}

# ============================================================================
# NVIDIA Driver Crash Recovery
# ============================================================================
# When the NVIDIA driver crashes (OOM, hardware error), nvidia-smi fails.
# The modules stay loaded but the GPU is unresponsive.
# This function detects that and reloads the driver.

reload_nvidia_driver() {
    log "============================================"
    log "NVIDIA DRIVER CRASH DETECTED"
    log "nvidia-smi has failed $nvidia_smi_failures consecutive times"
    log "Attempting driver reload..."
    log "============================================"

    # Step 1: Kill ALL GPU processes
    log "Stopping all AI services..."
    for svc in "${ALL_AI_SERVICES[@]}"; do
        systemctl stop "$svc" 2>/dev/null || true
    done
    sleep 3

    # Kill any remaining GPU processes
    while read -r pid; do
        [ -z "$pid" ] && continue
        local cmd
        cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
        if echo "$cmd" | grep -qiE "python|comfy|wan2|ollama|music|avatar|esrgan"; then
            log "  -> Killing before driver reload: PID $pid"
            kill -9 "$pid" 2>/dev/null || true
        fi
    done < <(pgrep -f 'python|ollama|comfyui' 2>/dev/null)

    sleep 2

    # Step 2: Unload NVIDIA modules
    log "Unloading NVIDIA kernel modules..."
    modprobe -r nvidia_uvm 2>/dev/null || true
    sleep 1
    modprobe -r nvidia_drm 2>/dev/null || true
    sleep 1
    modprobe -r nvidia_modeset 2>/dev/null || true
    sleep 1
    modprobe -r nvidia 2>/dev/null || true
    sleep 3

    # Verify modules unloaded
    if lsmod | grep -q nvidia; then
        log "WARNING: Some NVIDIA modules still loaded after rmmod"
        log "Forcing removal..."
        rmmod -f nvidia_uvm 2>/dev/null || true
        rmmod -f nvidia_drm 2>/dev/null || true
        rmmod -f nvidia_modeset 2>/dev/null || true
        rmmod -f nvidia 2>/dev/null || true
        sleep 2
    fi

    # Step 3: Reload NVIDIA modules
    log "Reloading NVIDIA kernel modules..."
    modprobe nvidia 2>/dev/null
    sleep 2
    modprobe nvidia_modeset 2>/dev/null
    sleep 1
    modprobe nvidia_drm 2>/dev/null
    sleep 1
    modprobe nvidia_uvm 2>/dev/null
    sleep 3

    # Step 4: Test if nvidia-smi works now
    if nvidia-smi -L >/dev/null 2>&1; then
        log "OK: NVIDIA driver reloaded successfully!"
        log "GPU: $(nvidia-smi -L 2>/dev/null)"
        nvidia_smi_failures=0
        nvidia_reload_failures=0
        return 0
    else
        log "FAIL: nvidia-smi still not working after driver reload"
        nvidia_reload_failures=$((nvidia_reload_failures + 1))

        if [ "$nvidia_reload_failures" -ge "$NVIDIA_RELOAD_FAIL_THRESHOLD" ]; then
            log "FATAL: NVIDIA driver reload failed $nvidia_reload_failures times"
            log "This likely requires a full reboot to recover."
            emergency_clean_reboot "NVIDIA driver unrecoverable"
        fi
        return 1
    fi
}

# ============================================================================
# Emergency Clean Reboot
# ============================================================================
emergency_clean_reboot() {
    local reason="${1:-VRAM critical}"
    log "============================================"
    log "EMERGENCY: $reason"
    log "Performing CLEAN REBOOT to prevent filesystem corruption"
    log "============================================"

    # Stop all AI services
    log "Stopping all AI services..."
    for svc in "${ALL_AI_SERVICES[@]}"; do
        systemctl stop "$svc" 2>/dev/null || true
    done

    sleep 5

    # CRITICAL: Sync filesystems before reboot
    log "Syncing filesystems (prevents corruption)..."
    sync
    sleep 2
    sync
    sleep 1

    # Log the reboot reason to kernel log (survives via pstore)
    echo "VRAM-WATCHDOG EMERGENCY REBOOT: $reason" > /dev/kmsg 2>/dev/null || true

    # Reboot
    log "Initiating clean reboot..."
    systemctl reboot 2>/dev/null || reboot -f

    # If reboot command fails, wait and try again
    sleep 10
    sync
    reboot -f

    # Last resort
    sleep 30
    echo b > /proc/sysrq-trigger 2>/dev/null || true
}

# ============================================================================
# Main watchdog loop
# ============================================================================

log "============================================"
log "VRAM Watchdog started (v2 - with driver crash recovery)"
log "  Check interval: ${CHECK_INTERVAL}s"
log "  Warn: ${WARN_THRESHOLD_PCT}% | Soft: ${SOFT_KILL_THRESHOLD_PCT}% | Hard: ${HARD_KILL_THRESHOLD_PCT}% | Reboot: ${CRITICAL_REBOOT_PCT}%"
log "  NVIDIA smi fail threshold: ${NVIDIA_SMI_FAIL_THRESHOLD}"
log "============================================"

consecutive_critical=0
MAX_CRITICAL_BEFORE_REBOOT=3
nvidia_smi_failures=0
nvidia_reload_failures=0
cycle_count=0

while true; do
    VRAM_INFO=$(get_vram_info)

    # ---- NVIDIA DRIVER CRASH DETECTION ----
    if [ -z "$VRAM_INFO" ]; then
        nvidia_smi_failures=$((nvidia_smi_failures + 1))

        if [ "$nvidia_smi_failures" -ge "$NVIDIA_SMI_FAIL_THRESHOLD" ]; then
            log "nvidia-smi failed ${nvidia_smi_failures} times. Driver may be crashed."
            reload_nvidia_driver
        else
            # Log only every few failures to avoid spam
            if [ $((nvidia_smi_failures % 2)) -eq 1 ]; then
                log "WARNING: nvidia-smi failed (${nvidia_smi_failures}/${NVIDIA_SMI_FAIL_THRESHOLD})"
            fi
        fi

        sleep "$CHECK_INTERVAL"
        continue
    fi

    # nvidia-smi works - reset failure counters
    if [ "$nvidia_smi_failures" -gt 0 ]; then
        log "nvidia-smi recovered after ${nvidia_smi_failures} failures"
        nvidia_smi_failures=0
    fi

    # ---- VRAM MONITORING ----
    USED_MB=$(echo "$VRAM_INFO" | awk '{print $1}')
    FREE_MB=$(echo "$VRAM_INFO" | awk '{print $2}')
    TOTAL_MB=$(echo "$VRAM_INFO" | awk '{print $3}')
    GPU_UTIL=$(echo "$VRAM_INFO" | awk '{print $4}')

    if [ "$TOTAL_MB" -gt 0 ] 2>/dev/null; then
        USAGE_PCT=$((USED_MB * 100 / TOTAL_MB))
    else
        USAGE_PCT=0
    fi

    # Normal logging every ~1 minute
    cycle_count=$((cycle_count + 1))
    if [ "$cycle_count" -ge 6 ]; then
        log "VRAM: ${USED_MB}MB / ${TOTAL_MB}MB (${USAGE_PCT}%) | GPU: ${GPU_UTIL}% | Free: ${FREE_MB}MB"
        cycle_count=0
    fi

    # Warning level
    if [ "$USAGE_PCT" -ge "$WARN_THRESHOLD_PCT" ] && [ "$USAGE_PCT" -lt "$SOFT_KILL_THRESHOLD_PCT" ]; then
        log "WARNING: VRAM at ${USAGE_PCT}% (${USED_MB}/${TOTAL_MB}MB)"
    fi

    # Soft kill level
    if [ "$USAGE_PCT" -ge "$SOFT_KILL_THRESHOLD_PCT" ] && [ "$USAGE_PCT" -lt "$HARD_KILL_THRESHOLD_PCT" ]; then
        log "SOFT KILL threshold: VRAM at ${USAGE_PCT}%"
        soft_kill_non_essential
        consecutive_critical=0
    fi

    # Hard kill level
    if [ "$USAGE_PCT" -ge "$HARD_KILL_THRESHOLD_PCT" ] && [ "$USAGE_PCT" -lt "$CRITICAL_REBOOT_PCT" ]; then
        log "HARD KILL threshold: VRAM at ${USAGE_PCT}%"
        hard_kill_all_non_protected
        consecutive_critical=0
    fi

    # Critical - potential reboot
    if [ "$USAGE_PCT" -ge "$CRITICAL_REBOOT_PCT" ]; then
        consecutive_critical=$((consecutive_critical + 1))
        log "CRITICAL: VRAM at ${USAGE_PCT}% (consecutive: ${consecutive_critical}/${MAX_CRITICAL_BEFORE_REBOOT})"

        hard_kill_all_non_protected

        sleep 5
        VRAM_INFO=$(get_vram_info)
        USED_MB=$(echo "$VRAM_INFO" | awk '{print $1}')
        TOTAL_MB=$(echo "$VRAM_INFO" | awk '{print $3}')
        if [ "$TOTAL_MB" -gt 0 ] 2>/dev/null; then
            USAGE_PCT=$((USED_MB * 100 / TOTAL_MB))
        fi

        if [ "$USAGE_PCT" -ge "$CRITICAL_REBOOT_PCT" ] && [ "$consecutive_critical" -ge "$MAX_CRITICAL_BEFORE_REBOOT" ]; then
            log "VRAM still at ${USAGE_PCT}% after ${consecutive_critical} consecutive critical states"
            emergency_clean_reboot "VRAM critical ${USAGE_PCT}% after all kills"
        else
            log "VRAM recovered to ${USAGE_PCT}% after kill - continuing"
        fi
    else
        consecutive_critical=0
    fi

    sleep "$CHECK_INTERVAL"
done
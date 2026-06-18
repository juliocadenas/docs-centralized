#!/bin/sh
# ============================================================================
# zz-auto-fsck - Auto filesystem check and repair in initramfs
# ============================================================================
# This script runs INSIDE the initramfs, BEFORE root is mounted.
# It ensures the root filesystem is ALWAYS checked and repaired automatically.
#
# CRITICAL: This prevents the server from dropping to busybox shell
#           when fsck encounters errors. Instead of waiting for manual
#           input, it auto-repairs and continues booting.
#
# Install location: /etc/initramfs-tools/scripts/init-premount/zz-auto-fsck
# After installing: sudo update-initramfs -u -k all
# ============================================================================

PREREQ=""

prereqs() {
    echo "$PREREQ"
}

case "$1" in
    prereqs)
        prereqs
        exit 0
        ;;
esac

# Source initramfs helpers
. /scripts/functions

# ============================================================================
# Configuration
# ============================================================================
LOG_PREFIX="[AUTO-FSCK]"
MAX_FSCK_RETRIES=3         # How many times to retry fsck if it fails
REBOOT_DELAY=10            # Seconds to wait before rebooting on fatal error

log() {
    echo "$LOG_PREFIX $*" >> /dev/kmsg 2>/dev/null || true
    echo "$LOG_PREFIX $*"
}

# ============================================================================
# Find root partition
# ============================================================================
find_root_partition() {
    # Method 1: From kernel cmdline (root= parameter)
    ROOT_PARAM=$(cat /proc/cmdline | grep -o 'root=[^ ]*' | head -1 | cut -d= -f2-)
    
    if [ -n "$ROOT_PARAM" ]; then
        # Handle UUID=xxx format
        case "$ROOT_PARAM" in
            UUID=*)
                UUID_VAL=$(echo "$ROOT_PARAM" | cut -d= -f2)
                # Find device by UUID
                for dev in /dev/sd*[0-9] /dev/nvme*p[0-9]; do
                    if [ -b "$dev" ]; then
                        DEV_UUID=$(blkid -s UUID -o value "$dev" 2>/dev/null)
                        if [ "$DEV_UUID" = "$UUID_VAL" ]; then
                            echo "$dev"
                            return 0
                        fi
                    fi
                done
                ;;
            /dev/*)
                echo "$ROOT_PARAM"
                return 0
                ;;
            LABEL=*)
                LABEL_VAL=$(echo "$ROOT_PARAM" | cut -d= -f2)
                for dev in /dev/sd*[0-9] /dev/nvme*p[0-9]; do
                    if [ -b "$dev" ]; then
                        DEV_LABEL=$(blkid -s LABEL -o value "$dev" 2>/dev/null)
                        if [ "$DEV_LABEL" = "$LABEL_VAL" ]; then
                            echo "$dev"
                            return 0
                        fi
                    fi
                done
                ;;
        esac
    fi
    
    # Method 2: Fallback - look for likely root partitions
    for dev in /dev/sda3 /dev/sda2 /dev/nvme0n1p3 /dev/nvme0n1p2; do
        if [ -b "$dev" ]; then
            echo "$dev"
            return 0
        fi
    done
    
    return 1
}

# ============================================================================
# Run fsck with auto-repair
# ============================================================================
run_fsck() {
    ROOT_DEV="$1"
    ATTEMPT=0
    
    while [ "$ATTEMPT" -lt "$MAX_FSCK_RETRIES" ]; do
        ATTEMPT=$((ATTEMPT + 1))
        log "Running fsck attempt $ATTEMPT/$MAX_FSCK_RETRIES on $ROOT_DEV"
        
        # Run fsck with -y (auto-repair all errors)
        # -y = answer yes to all questions
        # -C 0 = show progress (0 = none in initramfs)
        fsck -y "$ROOT_DEV" 2>&1 | while read -r line; do
            log "$line"
        done
        
        FSCK_EXIT=$?
        
        # fsck exit codes (bitmask):
        # 0 = no errors
        # 1 = errors corrected
        # 2 = system should be rebooted (errors corrected)
        # 4 = errors left uncorrected
        # 8 = operational error
        # 16 = usage error
        # 32 = canceled by user (shouldn't happen with -y)
        # 128 = shared library error
        
        case $FSCK_EXIT in
            0|1|2)
                log "fsck completed successfully (exit code: $FSCK_EXIT)"
                if [ "$FSCK_EXIT" -eq 2 ]; then
                    log "Filesystem was modified - proceeding (will be remounted fresh)"
                fi
                return 0
                ;;
            4)
                log "WARNING: fsck found errors it could NOT fix (exit 4)"
                log "Retrying (attempt $ATTEMPT)..."
                sleep 2
                ;;
            *)
                log "ERROR: fsck failed with exit code $FSCK_EXIT"
                log "Retrying (attempt $ATTEMPT)..."
                sleep 2
                ;;
        esac
    done
    
    log "FATAL: fsck failed after $MAX_FSCK_RETRIES attempts (last exit: $FSCK_EXIT)"
    return 1
}

# ============================================================================
# Safe reboot (fallback if everything fails)
# ============================================================================
emergency_reboot() {
    log "========================================"
    log "EMERGENCY REBOOT INITIATED"
    log "fsck could not repair filesystem."
    log "Server will reboot in $REBOOT_DELAY seconds."
    log "This prevents getting stuck in busybox."
    log "On next boot, fsck will try again."
    log "========================================"
    
    # Count down
    i=$REBOOT_DELAY
    while [ "$i" -gt 0 ]; do
        log "Rebooting in $i..."
        sleep 1
        i=$((i - 1))
    done
    
    # Force reboot
    # Try magic SysRq first (most reliable)
    if [ -e /proc/sysrq-trigger ]; then
        log "Triggering SysRq reboot..."
        echo 1 > /proc/sys/kernel/sysrq 2>/dev/null || true
        echo b > /proc/sysrq-trigger 2>/dev/null || true
    fi
    
    # Fallback: regular reboot
    log "Sending reboot command..."
    reboot -f
    
    # If nothing works, at least don't hang forever
    sleep 30
    log "Reboot command did not work. Hanging (but not in busybox)."
    while true; do sleep 60; done
}

# ============================================================================
# MAIN
# ============================================================================
log "============================================"
log "AUTO-FSCK: Starting automatic filesystem check"
log "============================================"

ROOT_DEV=$(find_root_partition)

if [ -z "$ROOT_DEV" ]; then
    log "ERROR: Could not determine root partition!"
    log "Kernel cmdline: $(cat /proc/cmdline)"
    log "Available devices:"
    ls /dev/sd* /dev/nvme* 2>/dev/null | while read -r d; do log "  $d"; done
    
    # Don't panic here - maybe the USB drive needs time to be detected
    log "Waiting 10s for devices to settle..."
    sleep 10
    
    ROOT_DEV=$(find_root_partition)
fi

if [ -z "$ROOT_DEV" ]; then
    log "STILL no root partition found after waiting."
    log "This might be a USB drive issue. Waiting 30 more seconds..."
    sleep 30
    ROOT_DEV=$(find_root_partition)
fi

if [ -n "$ROOT_DEV" ]; then
    log "Root partition found: $ROOT_DEV"
    
    if run_fsck "$ROOT_DEV"; then
        log "Filesystem check PASSED. Continuing boot normally."
        exit 0
    else
        log "Filesystem check FAILED after all retries."
        emergency_reboot
    fi
else
    log "CRITICAL: Cannot find root partition at all!"
    log "This may indicate a hardware failure (USB disconnect, dead disk)."
    log "Rebooting to try again..."
    emergency_reboot
fi

exit 0
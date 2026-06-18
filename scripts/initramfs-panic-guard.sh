#!/bin/sh
# ============================================================================
# zz-panic-guard - Prevent busybox shell drop on panic in initramfs
# ============================================================================
# This script runs INSIDE the initramfs, at the END (init-bottom phase),
# just before control is handed to the real init system.
#
# CRITICAL: This script overrides the panic() function so that if anything
#           in the boot process panics, instead of dropping to a busybox
#           shell (which requires physical keyboard intervention), it
#           automatically reboots after a short delay.
#
# Install location: /etc/initramfs-tools/scripts/init-bottom/zz-panic-guard
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

. /scripts/functions

# ============================================================================
# Override the panic function
# ============================================================================
# The default panic() in /scripts/functions drops to a shell.
# We override it BEFORE init takes over, so any panic during the
# critical handoff period auto-reboots instead.

log() {
    echo "[PANIC-GUARD] $*" >> /dev/kmsg 2>/dev/null || true
    echo "[PANIC-GUARD] $*"
}

# Save original panic function (for reference, not called)
if type panic >/dev/null 2>&1; then
    # shellcheck disable=SC2034
    ORIG_PANIC=panic
fi

# Override panic to auto-reboot instead of dropping to shell
panic() {
    log "============================================"
    log "PANIC INTERCEPTED - AUTO RECOVERY MODE"
    log "Reason: $*"
    log "Auto-rebooting in 10 seconds..."
    log "This prevents getting stuck in busybox shell"
    log "============================================"
    
    # Log to kernel message buffer (survives reboot via pstore if available)
    echo "AUTO-RECOVERY: Panic intercepted: $*" >> /dev/kmsg 2>/dev/null || true
    
    # Countdown
    i=10
    while [ "$i" -gt 0 ]; do
        log "Auto-reboot in $i..."
        sleep 1
        i=$((i - 1))
    done
    
    # Method 1: Magic SysRq (most reliable - works even if userspace is broken)
    if [ -e /proc/sysrq-trigger ]; then
        log "Triggering SysRq sync + reboot..."
        echo 1 > /proc/sys/kernel/sysrq 2>/dev/null || true
        echo s > /proc/sysrq-trigger 2>/dev/null || true  # Sync filesystems
        sleep 2
        echo u > /proc/sysrq-trigger 2>/dev/null || true  # Remount read-only
        sleep 1
        echo b > /proc/sysrq-trigger 2>/dev/null || true  # Reboot
    fi
    
    # Method 2: Direct reboot
    log "Trying reboot -f..."
    reboot -f
    
    # Method 3: Hard reboot via /proc
    log "Trying direct /proc reboot..."
    echo 1 > /proc/sys/kernel/sysrq 2>/dev/null || true
    echo b > /proc/sysrq-trigger 2>/dev/null || true
    
    # Last resort: hang without busybox
    log "All reboot methods exhausted. System halted (NOT in busybox)."
    log "Hardware watchdog or manual power cycle required."
    while true; do
        sleep 60
    done
}

# Export the new panic function so child processes inherit it
export -f panic 2>/dev/null || true

# Also set kernel panic parameters in case the kernel itself panics
# (not just initramfs scripts)
if [ -w /proc/sys/kernel/panic ]; then
    echo 10 > /proc/sys/kernel/panic 2>/dev/null || true
    log "Set kernel.panic=10 (auto-reboot after 10s on panic)"
fi

if [ -w /proc/sys/kernel/panic_on_oops ]; then
    echo 1 > /proc/sys/kernel/panic_on_oops 2>/dev/null || true
    log "Set kernel.panic_on_oops=1"
fi

# ============================================================================
# Disable interactive shell on errors
# ============================================================================
# Some initramfs scripts call "panic" which normally gives a shell.
# We've already overridden that. But also try to prevent any residual
# shell drops by setting a no-interactive environment.

# If there's a rescue shell function, override it too
if type rescue_shell >/dev/null 2>&1; then
    rescue_shell() {
        log "Rescue shell requested but BLOCKED by panic-guard"
        panic "Rescue shell blocked: $*"
    }
    export -f rescue_shell 2>/dev/null || true
fi

log "Panic guard installed. Any panic will auto-reboot instead of dropping to shell."
log "(kernel.panic=10, kernel.panic_on_oops=1)"

exit 0
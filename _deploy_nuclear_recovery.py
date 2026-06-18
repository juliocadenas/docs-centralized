#!/usr/bin/env python3
"""
=============================================================================
PLAN NUCLEAR - Deployment Script (v2 - based on real server audit)
=============================================================================
Based on actual audit of NAB9 (18/06/2026):

SERVER STATE:
  - Pop!_OS 24.04 LTS, kernel 6.18.7-76061807-generic
  - Root: /dev/sda3 (ext4, PNY SSD via USB bridge)
  - GPU: RTX 5080 (device 2c02) - CURRENTLY CRASHED (AER errors)
  - NVIDIA modules loaded but nvidia-smi fails
  - Services running that shouldn't be: avatar, avatar_services, ai-hub-effects, stt, tts
  - tune2fs -c 1 ALREADY configured (good)
  - All initramfs binaries present (fsck, blkid, etc.)
  - kernelstub config found and readable

CORRECTED PHASES:
  Phase 0: Immediate GPU recovery (driver is crashed NOW)
  Phase 1: Initramfs auto-fsck + panic-guard
  Phase 2: VRAM watchdog deployment
  Phase 3: Disable + stop services that cause OOM
  Phase 4: sysctl + filesystem hardening
  Phase 5: Verification
=============================================================================
"""

import paramiko
import os
import sys
import json
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ============================================================================
# Configuration (from audit)
# ============================================================================
HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

SCRIPTS_DIR = Path(__file__).parent / "scripts"

# Known server values from audit
ROOT_DEV = "/dev/sda3"
ROOT_UUID = "73b66df5-a1ca-428a-b006-fb8c396311ea"
KERNEL = "6.18.7-76061807-generic"

# Services that are ENABLED but should be DISABLED (cause VRAM OOM)
SERVICES_TO_DISABLE = [
    "comfyui",
    "wan2gp",
    "documusic-ensure",
    "musetalk",
    "latentsync",
    "liveportrait",
    "hallo2",
    "effects",
    "effects_services",
    "ai-hub-effects",
    "avatar",
    "avatar_services",
    "tts",
    "stt",
]

# Services that should stay ENABLED (safe, low VRAM)
SERVICES_KEEP = [
    "ollama",
    "ai-hub-gateway",
]

# ============================================================================
# SSH Helpers
# ============================================================================

def connect_ssh():
    print(f"\n  Connecting to {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USER, password=PASS, timeout=20)
    except Exception as e:
        print(f"  FAIL: Cannot connect: {e}")
        sys.exit(1)
    print("  OK: Connected!")
    return ssh


def run(ssh, cmd, timeout=120):
    """Run command with sudo password pipe."""
    full_cmd = f'echo {PASS} | sudo -S bash -c \'{cmd}\' 2>&1'
    try:
        _, stdout, _ = ssh.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        # Filter sudo password line
        lines = [l for l in out.split('\n') if '[sudo]' not in l and 'password for pepe' not in l.lower()]
        return '\n'.join(lines).strip()
    except Exception as e:
        return f"ERROR: {e}"


def run_nosudo(ssh, cmd, timeout=60):
    """Run command without sudo."""
    try:
        _, stdout, _ = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode('utf-8', errors='replace').strip()
    except Exception as e:
        return f"ERROR: {e}"


def run_verbose(ssh, cmd, label, timeout=120):
    out = run(ssh, cmd, timeout)
    status = "OK" if "ERROR" not in out[:20] else "FAIL"
    print(f"  [{status}] {label}")
    if out and len(out) > 0:
        for line in out.split("\n")[:4]:
            print(f"       {line}")
    return out


def upload_file(ssh, local_path, remote_path, mode="0644"):
    sftp = ssh.open_sftp()
    sftp.put(str(local_path), remote_path)
    sftp.chmod(remote_path, int(mode, 8))
    sftp.close()


def upload_content(ssh, content, remote_path, mode="0644"):
    sftp = ssh.open_sftp()
    with sftp.file(remote_path, 'w') as f:
        f.write(content)
    sftp.chmod(remote_path, int(mode, 8))
    sftp.close()


# ============================================================================
# PHASE 0: Immediate GPU Recovery
# ============================================================================

def phase0_gpu_recovery(ssh, dry_run=False):
    """The GPU is crashed RIGHT NOW. Recover it before doing anything else."""
    print("\n" + "=" * 70)
    print("  PHASE 0: Immediate GPU Recovery")
    print("  (nvidia-smi is failing with AER errors)")
    print("=" * 70)

    if dry_run:
        print("  [DRY RUN] Would:")
        print("    - Stop all AI services")
        print("    - Unload NVIDIA kernel modules")
        print("    - Reload NVIDIA kernel modules")
        print("    - Verify nvidia-smi works")
        return True

    # Check current GPU status
    gpu_check = run_nosudo(ssh, "nvidia-smi -L 2>&1")
    print(f"\n  Current GPU status: {gpu_check[:100]}")

    if "GPU" in gpu_check and "Error" not in gpu_check:
        print("  GPU is already working! Skipping recovery.")
        return True

    print("\n  GPU IS CRASHED. Starting recovery...")

    # Step 1: Stop ALL AI services
    print("\n  Step 1: Stopping all AI services...")
    for svc in SERVICES_TO_DISABLE + SERVICES_KEEP:
        run(ssh, f"systemctl stop {svc} 2>/dev/null")
    # Kill any GPU python processes
    run(ssh, "pkill -9 -f 'comfyui|wan2|documusic|musetalk|latentsync|liveportrait|hallo2|avatar|effects|whisper|piper' 2>/dev/null || true")
    time.sleep(3)

    # Step 2: Unload NVIDIA modules
    print("\n  Step 2: Unloading NVIDIA kernel modules...")
    run(ssh, "modprobe -r nvidia_uvm 2>/dev/null || true")
    time.sleep(1)
    run(ssh, "modprobe -r nvidia_drm 2>/dev/null || true")
    time.sleep(1)
    run(ssh, "modprobe -r nvidia_modeset 2>/dev/null || true")
    time.sleep(1)
    run(ssh, "modprobe -r nvidia 2>/dev/null || true")
    time.sleep(3)

    # Check if modules unloaded
    modules = run(ssh, "lsmod | grep nvidia")
    if modules:
        print(f"  WARNING: Modules still loaded:\n    {modules}")
        # Force remove
        run(ssh, "rmmod -f nvidia_uvm nvidia_drm nvidia_modeset nvidia 2>/dev/null || true")
        time.sleep(2)

    # Step 3: Reload NVIDIA modules
    print("\n  Step 3: Reloading NVIDIA kernel modules...")
    run(ssh, "modprobe nvidia 2>/dev/null")
    time.sleep(2)
    run(ssh, "modprobe nvidia_modeset 2>/dev/null")
    time.sleep(1)
    run(ssh, "modprobe nvidia_drm 2>/dev/null")
    time.sleep(1)
    run(ssh, "modprobe nvidia_uvm 2>/dev/null")
    time.sleep(5)

    # Step 4: Verify
    print("\n  Step 4: Verifying GPU recovery...")
    gpu_check = run_nosudo(ssh, "nvidia-smi -L 2>&1")
    print(f"  Result: {gpu_check}")

    if "GPU" in gpu_check and "Error" not in gpu_check:
        print("  OK: GPU recovered successfully!")
        # Start essential services
        run(ssh, "systemctl start ollama")
        time.sleep(3)
        run(ssh, "systemctl start ai-hub-gateway")
        time.sleep(2)
        return True
    else:
        print("  WARNING: GPU did not recover with driver reload.")
        print("  A reboot may be required to fully reset the GPU.")
        print("  Continuing with deployment anyway - watchdog will handle it.")
        return False


# ============================================================================
# PHASE 1: Initramfs Auto-Recovery
# ============================================================================

def phase1_initramfs(ssh, dry_run=False):
    """Deploy initramfs auto-fsck and panic-guard scripts."""
    print("\n" + "=" * 70)
    print("  PHASE 1: Initramfs Auto-Recovery (the core fix)")
    print("=" * 70)

    if dry_run:
        print("  [DRY RUN] Would install:")
        print(f"    - scripts/init-premount/zz-auto-fsck")
        print(f"    - scripts/init-bottom/zz-panic-guard")
        print(f"    - Add panic=10, fsck.mode=force to kernelstub")
        print(f"    - Rebuild initramfs")
        return True

    # Step 1: Upload scripts
    print("\n  Step 1: Installing initramfs scripts...")

    # auto-fsck (runs BEFORE root is mounted)
    auto_fsck = SCRIPTS_DIR / "initramfs-auto-fsck.sh"
    if not auto_fsck.exists():
        print(f"  FAIL: Missing {auto_fsck}")
        return False

    upload_file(ssh, auto_fsck, "/tmp/zz-auto-fsck", mode="0755")
    run_verbose(ssh, "mkdir -p /etc/initramfs-tools/scripts/init-premount && cp /tmp/zz-auto-fsck /etc/initramfs-tools/scripts/init-premount/zz-auto-fsck && chmod +x /etc/initramfs-tools/scripts/init-premount/zz-auto-fsck",
                "Installed init-premount/zz-auto-fsck")

    # panic-guard (runs at the end of initramfs, overrides panic function)
    panic_guard = SCRIPTS_DIR / "initramfs-panic-guard.sh"
    if not panic_guard.exists():
        print(f"  FAIL: Missing {panic_guard}")
        return False

    upload_file(ssh, panic_guard, "/tmp/zz-panic-guard", mode="0755")
    run_verbose(ssh, "mkdir -p /etc/initramfs-tools/scripts/init-bottom && cp /tmp/zz-panic-guard /etc/initramfs-tools/scripts/init-bottom/zz-panic-guard && chmod +x /etc/initramfs-tools/scripts/init-bottom/zz-panic-guard",
                "Installed init-bottom/zz-panic-guard")

    # Step 2: Update kernelstub configuration
    print("\n  Step 2: Updating kernel parameters via kernelstub...")

    # Read current config
    config_raw = run_nosudo(ssh, "cat /etc/kernelstub/configuration")
    try:
        config = json.loads(config_raw)
    except json.JSONDecodeError:
        print(f"  FAIL: Cannot parse kernelstub config")
        print(f"  Raw: {config_raw[:200]}")
        return False

    user_opts = config.get("user", {}).get("kernel_options", [])
    print(f"  Current kernel options: {user_opts}")

    # Add our parameters
    new_params = {
        "panic=10": "Auto-reboot 10s after kernel panic",
        "fsck.mode=force": "Force filesystem check on every boot",
        "fsck.repair=yes": "Auto-repair filesystem errors",
    }

    added = []
    for param, desc in new_params.items():
        if param not in user_opts:
            user_opts.append(param)
            added.append(param)
            print(f"  Adding: {param} ({desc})")

    if added:
        config["user"]["kernel_options"] = user_opts

        # Write new config
        new_config_json = json.dumps(config, indent=2)
        upload_content(ssh, new_config_json, "/tmp/kernelstub_new.json")

        # Backup and replace
        run(ssh, "cp /etc/kernelstub/configuration /etc/kernelstub/configuration.bak.$(date +%Y%m%d%H%M%S)")
        run_verbose(ssh, "cp /tmp/kernelstub_new.json /etc/kernelstub/configuration",
                    "Updated kernelstub configuration")

        # Apply with kernelstub
        print("\n  Running kernelstub to apply...")
        result = run(ssh, "kernelstub 2>&1")
        print(f"  kernelstub output: {result[:300]}")
    else:
        print("  All parameters already present.")

    # Step 3: Rebuild initramfs
    print("\n  Step 3: Rebuilding initramfs (this takes 30-60 seconds)...")
    result = run(ssh, "update-initramfs -u -k all 2>&1", timeout=180)
    print(f"  update-initramfs: {result[:300]}")

    # Step 4: Verify scripts are in initramfs
    print("\n  Step 4: Verifying scripts embedded in initramfs...")
    verify = run(ssh, f"lsinitramfs /boot/initrd.img-{KERNEL} 2>/dev/null | grep -E 'auto-fsck|panic-guard'")
    if verify:
        print("  OK: Scripts found in initramfs:")
        for line in verify.split("\n"):
            print(f"    {line}")
    else:
        print("  WARNING: Scripts NOT found in initramfs!")
        print("  Trying alternative verification...")
        verify2 = run(ssh, f"lsinitramfs /boot/initrd.img-$(uname -r) 2>/dev/null | grep scripts")
        print(f"  Scripts in initramfs: {verify2[:300]}")

    # Step 5: Verify kernel cmdline
    print("\n  Step 5: Verifying kernel cmdline...")
    cmdline = run_nosudo(ssh, "cat /proc/cmdline")
    print(f"  Current: {cmdline}")

    return True


# ============================================================================
# PHASE 2: VRAM Watchdog
# ============================================================================

def phase2_watchdog(ssh, dry_run=False):
    """Deploy the VRAM watchdog service."""
    print("\n" + "=" * 70)
    print("  PHASE 2: VRAM Watchdog (OS-level protection)")
    print("=" * 70)

    if dry_run:
        print("  [DRY RUN] Would install vram-watchdog.sh + service")
        return True

    # Upload watchdog script
    print("\n  Step 1: Installing watchdog script...")
    watchdog = SCRIPTS_DIR / "vram-watchdog.sh"
    if not watchdog.exists():
        print(f"  FAIL: Missing {watchdog}")
        return False

    upload_file(ssh, watchdog, "/tmp/vram-watchdog.sh", mode="0755")
    run_verbose(ssh, "cp /tmp/vram-watchdog.sh /usr/local/bin/vram-watchdog.sh && chmod +x /usr/local/bin/vram-watchdog.sh",
                "Installed /usr/local/bin/vram-watchdog.sh")

    # Upload service file
    print("\n  Step 2: Installing systemd service...")
    service = SCRIPTS_DIR / "vram-watchdog.service"
    if not service.exists():
        print(f"  FAIL: Missing {service}")
        return False

    upload_file(ssh, service, "/tmp/vram-watchdog.service", mode="0644")
    run_verbose(ssh, "cp /tmp/vram-watchdog.service /etc/systemd/system/vram-watchdog.service",
                "Installed vram-watchdog.service")

    # Enable and start
    print("\n  Step 3: Enabling and starting watchdog...")
    run(ssh, "systemctl daemon-reload")
    run_verbose(ssh, "systemctl enable vram-watchdog", "Enabled at boot")
    run_verbose(ssh, "systemctl start vram-watchdog", "Started")

    time.sleep(3)
    status = run_nosudo(ssh, "systemctl is-active vram-watchdog")
    if "active" in status:
        print("  OK: VRAM watchdog is running!")
    else:
        print(f"  WARNING: Status: {status}")
        logs = run(ssh, "journalctl -u vram-watchdog --no-pager -n 15")
        print(f"  Logs:\n{logs}")

    return True


# ============================================================================
# PHASE 3: Service Hardening
# ============================================================================

def phase3_services(ssh, dry_run=False):
    """Disable services that cause VRAM OOM. Install OOM protection."""
    print("\n" + "=" * 70)
    print("  PHASE 3: Service Hardening (disable OOM-causing services)")
    print("=" * 70)

    if dry_run:
        print("  [DRY RUN] Would:")
        print(f"    - Disable {len(SERVICES_TO_DISABLE)} services")
        print(f"    - Install OOM protection for ollama and gateway")
        return True

    # Disable services
    print(f"\n  Step 1: Disabling {len(SERVICES_TO_DISABLE)} heavy services...")
    for svc in SERVICES_TO_DISABLE:
        result = run(ssh, f"systemctl disable {svc} 2>&1")
        result2 = run(ssh, f"systemctl stop {svc} 2>&1")
        if "Removed" in result or "disabled" in result.lower() or "not-found" in result.lower():
            print(f"    OK: {svc} disabled")
        else:
            print(f"    {svc}: {result[:80]}")

    # Install OOM protection for Ollama
    print("\n  Step 2: Installing OOM protection for critical services...")

    ollama_dropin = """[Service]
OOMScoreAdjust=-1000
OOMPolicy=continue
"""
    run(ssh, "mkdir -p /etc/systemd/system/ollama.service.d/")
    upload_content(ssh, ollama_dropin, "/tmp/oom-ollama.conf")
    run_verbose(ssh, "cp /tmp/oom-ollama.conf /etc/systemd/system/ollama.service.d/oom-protect.conf",
                "Ollama OOM protection")

    gateway_dropin = """[Service]
OOMScoreAdjust=-500
MemoryMax=4G
MemoryHigh=3G
OOMPolicy=stop
"""
    run(ssh, "mkdir -p /etc/systemd/system/ai-hub-gateway.service.d/")
    upload_content(ssh, gateway_dropin, "/tmp/oom-gateway.conf")
    run_verbose(ssh, "cp /tmp/oom-gateway.conf /etc/systemd/system/ai-hub-gateway.service.d/oom-protect.conf",
                "Gateway OOM protection")

    run(ssh, "systemctl daemon-reload")

    return True


# ============================================================================
# PHASE 4: Filesystem + sysctl Hardening
# ============================================================================

def phase4_hardening(ssh, dry_run=False):
    """Apply sysctl and filesystem hardening."""
    print("\n" + "=" * 70)
    print("  PHASE 4: Filesystem + sysctl Hardening")
    print("=" * 70)

    if dry_run:
        print("  [DRY RUN] Would install sysctl + verify tune2fs")
        return True

    # Install sysctl config
    print("\n  Step 1: Installing sysctl config...")
    sysctl_conf = SCRIPTS_DIR / "99-panic-reboot.conf"
    if sysctl_conf.exists():
        upload_file(ssh, sysctl_conf, "/tmp/99-panic-reboot.conf")
    else:
        # Inline
        upload_content(ssh, """# Kernel panic auto-reboot
kernel.panic = 10
kernel.panic_on_oops = 1
kernel.sysrq = 1
fs.inotify.max_user_watches = 524288
""", "/tmp/99-panic-reboot.conf")

    run_verbose(ssh, "cp /tmp/99-panic-reboot.conf /etc/sysctl.d/99-panic-reboot.conf",
                "Installed sysctl config")

    result = run(ssh, "sysctl --system 2>&1 | tail -5")
    print(f"  sysctl apply: {result[:200]}")

    # Verify tune2fs (already configured per audit, but verify)
    print(f"\n  Step 2: Verifying tune2fs on {ROOT_DEV}...")
    tune = run(ssh, f"tune2fs -l {ROOT_DEV} 2>/dev/null | grep -iE 'mount count|maximum|state|error'")
    print(f"  tune2fs: {tune}")

    if "Maximum mount count:      1" in tune:
        print("  OK: tune2fs already configured for fsck on every boot")
    else:
        print("  Setting tune2fs -c 1...")
        run_verbose(ssh, f"tune2fs -c 1 {ROOT_DEV}", "Set fsck every boot")

    return True


# ============================================================================
# PHASE 5: Verification
# ============================================================================

def phase5_verify(ssh, dry_run=False):
    """Verify everything is correctly deployed."""
    print("\n" + "=" * 70)
    print("  PHASE 5: Verification")
    print("=" * 70)

    if dry_run:
        print("  [DRY RUN] Skipping")
        return True

    passed = 0
    failed = 0

    def check(label, ok, detail=""):
        nonlocal passed, failed
        if ok:
            print(f"  [PASS] {label}")
            passed += 1
        else:
            print(f"  [FAIL] {label} {detail}")
            failed += 1

    # 1. Initramfs scripts
    print("\n  Check 1: Initramfs scripts...")
    result = run(ssh, f"lsinitramfs /boot/initrd.img-{KERNEL} 2>/dev/null | grep -E 'auto-fsck|panic-guard'")
    check("auto-fsck in initramfs", "auto-fsck" in (result or ""))
    check("panic-guard in initramfs", "panic-guard" in (result or ""))

    # 2. Kernel cmdline
    print("\n  Check 2: Kernel parameters...")
    cmdline = run_nosudo(ssh, "cat /proc/cmdline")
    check("panic=10 in cmdline", "panic=10" in (cmdline or ""))
    check("fsck.mode=force in cmdline", "fsck.mode=force" in (cmdline or ""))

    # 3. VRAM watchdog
    print("\n  Check 3: VRAM watchdog...")
    status = run_nosudo(ssh, "systemctl is-active vram-watchdog")
    check("Watchdog running", status.strip() == "active", f"(status: {status})")

    enabled = run_nosudo(ssh, "systemctl is-enabled vram-watchdog")
    check("Watchdog enabled", "enabled" in (enabled or ""))

    # 4. sysctl
    print("\n  Check 4: Sysctl settings...")
    panic = run_nosudo(ssh, "sysctl -n kernel.panic")
    check("kernel.panic=10", panic.strip() == "10", f"(got: {panic})")

    oops = run_nosudo(ssh, "sysctl -n kernel.panic_on_oops")
    check("kernel.panic_on_oops=1", oops.strip() == "1", f"(got: {oops})")

    # 5. Services disabled
    print("\n  Check 5: Services disabled...")
    for svc in SERVICES_TO_DISABLE:
        status = run_nosudo(ssh, f"systemctl is-enabled {svc} 2>/dev/null")
        check(f"{svc} disabled", "disabled" in (status or "") or "not-found" in (status or ""),
              f"(status: {status})")

    # 6. tune2fs
    print("\n  Check 6: Filesystem fsck...")
    tune = run(ssh, f"tune2fs -l {ROOT_DEV} 2>/dev/null | grep 'Maximum mount count'")
    check("tune2fs -c 1", "1" in (tune or ""), f"({tune})")

    # 7. GPU status
    print("\n  Check 7: GPU status...")
    gpu = run_nosudo(ssh, "nvidia-smi -L 2>&1")
    check("GPU accessible", "GPU" in (gpu or "") and "Error" not in (gpu or ""), f"({gpu[:80]})")

    # Summary
    print("\n" + "=" * 70)
    total = passed + failed
    print(f"  VERIFICATION: {passed}/{total} passed")
    if failed == 0:
        print("  ALL CHECKS PASSED!")
    else:
        print(f"  {failed} checks need attention")
    print("=" * 70)

    return failed == 0


# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deploy Nuclear Recovery System to NAB9")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--phase", type=int, choices=[0,1,2,3,4,5], help="Deploy only one phase")
    parser.add_argument("--no-reboot-gpu", action="store_true", help="Skip Phase 0 (GPU recovery)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print("=" * 70)
    print("  PLAN NUCLEAR - Deployment (v2 - audited)")
    print("=" * 70)
    print(f"  Target: {HOST}")
    print(f"  Root: {ROOT_DEV} (ext4)")
    print(f"  Kernel: {KERNEL}")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    ssh = connect_ssh()

    # Preflight
    print("\n  Preflight checks...")
    uptime = run_nosudo(ssh, "uptime")
    print(f"  {uptime}")
    disk = run_nosudo(ssh, "df -h /")
    print(f"  {disk}")

    if not args.dry_run and not args.yes:
        print("\n" + "=" * 70)
        print("  WARNING: This modifies initramfs and kernel boot parameters.")
        print("  A reboot is recommended after deployment to test recovery.")
        print("  Ensure you have console/physical access in case of issues.")
        print("=" * 70)
        response = input("\n  Type 'DEPLOY' to continue: ")
        if response.strip().upper() != "DEPLOY":
            print("  Aborted.")
            ssh.close()
            return

    success = True

    # Phase 0: GPU recovery (if GPU is down)
    if (args.phase is None or args.phase == 0) and not args.no_reboot_gpu:
        success = phase0_gpu_recovery(ssh, args.dry_run) and success

    # Phase 1: Initramfs
    if args.phase is None or args.phase == 1:
        success = phase1_initramfs(ssh, args.dry_run) and success

    # Phase 2: Watchdog
    if args.phase is None or args.phase == 2:
        success = phase2_watchdog(ssh, args.dry_run) and success

    # Phase 3: Services
    if args.phase is None or args.phase == 3:
        success = phase3_services(ssh, args.dry_run) and success

    # Phase 4: Hardening
    if args.phase is None or args.phase == 4:
        success = phase4_hardening(ssh, args.dry_run) and success

    # Phase 5: Verify
    if args.phase is None or args.phase == 5:
        success = phase5_verify(ssh, args.dry_run) and success

    # Final
    print("\n" + "=" * 70)
    if success:
        print("  DEPLOYMENT COMPLETE!")
        if not args.dry_run:
            print("\n  NEXT STEPS:")
            print("    1. Reboot to test: ssh pepe@100.105.27.27 'sudo reboot'")
            print("    2. Wait 2-3 min")
            print("    3. Check: ssh pepe@100.105.27.27 'systemctl status vram-watchdog'")
            print("    4. Check: ssh pepe@100.105.27.27 'nvidia-smi'")
    else:
        print("  DEPLOYMENT COMPLETED WITH WARNINGS - review above")
    print("=" * 70)

    ssh.close()
    print("\n  Disconnected.")


if __name__ == "__main__":
    main()
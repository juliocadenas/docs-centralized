#!/usr/bin/env python3
"""Fix the 5 remaining issues from deployment."""
import paramiko, sys, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PASS = "pepe1234"
HOST = "100.105.27.27"
USER = "pepe"
KERNEL = "6.18.7-76061807-generic"
ROOT_DEV = "/dev/sda3"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=20)

def run(cmd, timeout=120):
    """Run with proper quoting - use heredoc to avoid pipe issues."""
    # Write command to a temp script and execute it
    import base64
    encoded = base64.b64encode(cmd.encode()).decode()
    full_cmd = f'echo {PASS} | sudo -S bash -c "eval \'$(echo {encoded} | base64 -d)\'" 2>&1'
    try:
        _, stdout, _ = ssh.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        lines = [l for l in out.split('\n') if '[sudo]' not in l and 'password for pepe' not in l.lower()]
        return '\n'.join(lines).strip()
    except Exception as e:
        return f"ERROR: {e}"

def run_nosudo(cmd, timeout=60):
    try:
        _, stdout, _ = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode('utf-8', errors='replace').strip()
    except Exception as e:
        return f"ERROR: {e}"

print("=" * 60)
print("  FIXING 5 REMAINING ISSUES")
print("=" * 60)

# ---- FIX 1: Verify auto-fsck is actually in initramfs ----
print("\n[FIX 1] Verifying initramfs scripts (proper quoting)...")
result = run(f'lsinitramfs /boot/initrd.img-{KERNEL} 2>/dev/null | grep -c auto-fsck')
print(f"  auto-fsck count in initramfs: {result}")
result2 = run(f'lsinitramfs /boot/initrd.img-{KERNEL} 2>/dev/null | grep -c panic-guard')
print(f"  panic-guard count in initramfs: {result2}")

# Show actual paths
result3 = run(f'lsinitramfs /boot/initrd.img-{KERNEL} 2>/dev/null | grep -E "auto.fsck|panic.guard"')
print(f"  Paths:\n    {result3}")

# ---- FIX 2: Run kernelstub explicitly to apply boot params ----
print("\n[FIX 2] Running kernelstub to apply boot parameters...")
kresult = run('kernelstub 2>&1')
print(f"  kernelstub: {kresult[:500]}")

# Verify the EFI cmdline file was updated
print("\n  Checking EFI cmdline files...")
efi_result = run('find /boot/efi/EFI/ -name cmdline -exec echo {} \\; -exec cat {} \\; 2>/dev/null')
print(f"  EFI cmdline: {efi_result[:500]}")

# ---- FIX 3: Verify tune2fs properly ----
print(f"\n[FIX 3] Verifying tune2fs on {ROOT_DEV}...")
tune_result = run(f'tune2fs -l {ROOT_DEV} 2>/dev/null')
# Extract relevant lines
for line in tune_result.split('\n'):
    if 'ount' in line or 'tate' in line or 'rror' in line:
        print(f"  {line.strip()}")

# ---- FIX 4: Check current running kernel cmdline ----
print("\n[FIX 4] Current kernel cmdline (needs reboot to update):")
cmdline = run_nosudo('cat /proc/cmdline')
print(f"  {cmdline}")
print("  NOTE: New params (panic=10, fsck.mode=force) will be active after REBOOT")

# ---- FIX 5: GPU requires reboot ----
print("\n[FIX 5] GPU Status:")
gpu = run_nosudo('nvidia-smi -L 2>&1')
print(f"  {gpu}")
print("  NOTE: GPU requires REBOOT to recover from AER crash")

# ---- SUMMARY ----
print("\n" + "=" * 60)
print("  STATUS SUMMARY")
print("=" * 60)

# Check what's actually deployed
checks = []

# auto-fsck in initramfs
af = run(f'lsinitramfs /boot/initrd.img-{KERNEL} 2>/dev/null | grep auto-fsck | wc -l')
checks.append(("auto-fsck in initramfs", int(af) > 0 if af.isdigit() else False))

# panic-guard in initramfs
pg = run(f'lsinitramfs /boot/initrd.img-{KERNEL} 2>/dev/null | grep panic-guard | wc -l')
checks.append(("panic-guard in initramfs", int(pg) > 0 if pg.isdigit() else False))

# kernelstub config has params
ksc = run_nosudo('cat /etc/kernelstub/configuration')
checks.append(("panic=10 in kernelstub config", 'panic=10' in ksc))
checks.append(("fsck.mode=force in kernelstub config", 'fsck.mode=force' in ksc))

# VRAM watchdog running
wd = run_nosudo('systemctl is-active vram-watchdog')
checks.append(("VRAM watchdog running", wd.strip() == 'active'))

# sysctl
kp = run_nosudo('sysctl -n kernel.panic')
checks.append(("kernel.panic=10 (live)", kp.strip() == "10"))

# All services disabled
all_disabled = True
for svc in ['comfyui','wan2gp','documusic-ensure','musetalk','latentsync','liveportrait',
            'hallo2','effects','effects_services','ai-hub-effects','avatar','avatar_services','tts','stt']:
    s = run_nosudo(f'systemctl is-enabled {svc} 2>/dev/null')
    if 'enabled' in s and 'disabled' not in s:
        all_disabled = False
        break
checks.append(("All 14 heavy services disabled", all_disabled))

# tune2fs -c 1
tc = run(f'tune2fs -l {ROOT_DEV} 2>/dev/null | grep "Maximum mount count"')
checks.append(("tune2fs -c 1", "1" in tc))

# Print results
passed = sum(1 for _, ok in checks if ok)
for label, ok in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")

print(f"\n  {passed}/{len(checks)} checks passed")

# What needs reboot
print("\n" + "=" * 60)
print("  REQUIRES REBOOT TO ACTIVATE:")
print("    - panic=10 and fsck.mode=force in actual kernel cmdline")
print("    - NVIDIA GPU recovery (from AER crash)")
print("    - All initramfs changes take effect on next boot")
print("=" * 60)

ssh.close()
print("\n  Done.")
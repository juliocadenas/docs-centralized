#!/usr/bin/env python3
"""Post-reboot verification - writes output to file to avoid buffering."""
import paramiko, sys, time

PASS = "pepe1234"
HOST = "100.105.27.27"
OUTPUT_FILE = "post_reboot_status.txt"

lines = []
def log(msg):
    lines.append(str(msg))
    print(msg)

log("=" * 60)
log("  POST-REBOOT VERIFICATION")
log("=" * 60)

# Try to connect
for attempt in range(3):
    try:
        log(f"\nConnecting (attempt {attempt+1})...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username='pepe', password=PASS, timeout=15)
        log("Connected!")
        break
    except Exception as e:
        log(f"  Failed: {e}")
        time.sleep(10)
else:
    log("CANNOT CONNECT after 3 attempts. Server may still be booting.")
    with open(OUTPUT_FILE, 'w') as f:
        f.write('\n'.join(lines))
    sys.exit(1)

def run(cmd):
    try:
        _, stdout, _ = ssh.exec_command(cmd, timeout=30)
        return stdout.read().decode('utf-8', errors='replace').strip()
    except Exception as e:
        return f"ERROR: {e}"

# 1. Uptime
log("\n--- UPTIME ---")
uptime = run("uptime")
log(uptime)

# Check if it actually rebooted (uptime should be < 5 min)
if "min" in uptime:
    log("  >>> Server DID reboot recently!")
else:
    log("  >>> WARNING: Server may NOT have rebooted!")

# 2. Kernel cmdline
log("\n--- KERNEL CMDLINE ---")
cmdline = run("cat /proc/cmdline")
log(cmdline)

has_panic = "panic=10" in cmdline
has_fsck = "fsck.mode=force" in cmdline
has_repair = "fsck.repair=yes" in cmdline

log(f"\n  panic=10: {'PASS' if has_panic else 'FAIL'}")
log(f"  fsck.mode=force: {'PASS' if has_fsck else 'FAIL'}")
log(f"  fsck.repair=yes: {'PASS' if has_repair else 'FAIL'}")

# 3. GPU
log("\n--- GPU STATUS ---")
gpu = run("nvidia-smi -L 2>&1")
log(gpu)
if "GPU" in gpu and "Error" not in gpu:
    log("  >>> GPU RECOVERED! 🎉")
    # Get VRAM info
    gpu_full = run("nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader 2>&1")
    log(f"  VRAM: {gpu_full}")
else:
    log("  >>> GPU still crashed :(")

# 4. VRAM Watchdog
log("\n--- VRAM WATCHDOG ---")
wd = run("systemctl is-active vram-watchdog")
log(f"  Active: {wd}")

# 5. Ollama
log("\n--- OLLAMA ---")
ollama = run("systemctl is-active ollama")
log(f"  Active: {ollama}")

# 6. Gateway
log("\n--- AI HUB GATEWAY ---")
gw = run("systemctl is-active ai-hub-gateway")
log(f"  Active: {gw}")

# 7. Services still disabled?
log("\n--- SERVICES STATUS ---")
for svc in ['comfyui','wan2gp','musetalk','latentsync','liveportrait','hallo2',
            'effects','ai-hub-effects','avatar','avatar_services','tts','stt']:
    s = run(f"systemctl is-enabled {svc} 2>/dev/null")
    a = run(f"systemctl is-active {svc} 2>/dev/null")
    log(f"  {svc}: {s} / {a}")

# 8. Filesystem state
log("\n--- FILESYSTEM ---")
fs = run("df -h /")
log(fs)

# 9. dmesg for boot messages
log("\n--- BOOT LOGS (last 20 lines) ---")
dmesg = run("dmesg 2>/dev/null | tail -20 || journalctl -b --no-pager | tail -20")
for line in dmesg.split('\n'):
    log(f"  {line}")

# Summary
log("\n" + "=" * 60)
log("  SUMMARY")
log("=" * 60)
checks = [
    ("Server rebooted", "min" in uptime),
    ("panic=10 active", has_panic),
    ("fsck.mode=force active", has_fsck),
    ("GPU recovered", "GPU" in gpu and "Error" not in gpu),
    ("VRAM watchdog running", wd.strip() == "active"),
]
for label, ok in checks:
    log(f"  [{'PASS' if ok else 'FAIL'}] {label}")

passed = sum(1 for _, ok in checks if ok)
log(f"\n  {passed}/{len(checks)} passed")

ssh.close()

# Write to file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

log(f"\n  Status written to {OUTPUT_FILE}")
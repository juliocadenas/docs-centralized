#!/usr/bin/env python3
"""Deploy GPU optimizations + Tailscale keepalive to NAB9."""
import paramiko
import sys
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SSH_HOST = '100.105.27.27'
SSH_USER = 'pepe'
SSH_PASS = 'pepe1234'
REMOTE_DIR = '/mnt/seagate/ai-hub-gateway'

files_to_deploy = [
    ('ai-hub-gateway/gateway/gpu_manager.py', f'{REMOTE_DIR}/gateway/gpu_manager.py'),
    ('ai-hub-gateway/gateway/config.py', f'{REMOTE_DIR}/gateway/config.py'),
    ('ai-hub-gateway/main.py', f'{REMOTE_DIR}/main.py'),
    ('ai-hub-gateway/gateway/routers/images.py', f'{REMOTE_DIR}/gateway/routers/images.py'),
    ('ai-hub-gateway/gateway/routers/audio.py', f'{REMOTE_DIR}/gateway/routers/audio.py'),
    ('ai-hub-gateway/gateway/routers/video.py', f'{REMOTE_DIR}/gateway/routers/video.py'),
    ('health_check.sh', '/tmp/tailscale_keepalive.sh'),
]

print("=== Connecting to NAB9 ===")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=15)
except Exception as e:
    print(f"ERROR: Cannot connect - {e}")
    sys.exit(1)

print("Connected!\n")

# Upload files
sftp = ssh.open_sftp()
for local_path, remote_path in files_to_deploy:
    if os.path.exists(local_path):
        print(f"  Uploading {local_path} -> {remote_path}")
        sftp.put(local_path, remote_path)
    else:
        print(f"  SKIP {local_path} (not found)")
sftp.close()

# Install Tailscale keepalive cron
print("\n=== Installing Tailscale keepalive ===")
commands = [
    "sudo cp /tmp/tailscale_keepalive.sh /mnt/seagate/scripts/tailscale_keepalive.sh",
    "sudo chmod +x /mnt/seagate/scripts/tailscale_keepalive.sh",
    "(crontab -l 2>/dev/null | grep -v tailscale_keepalive; echo '*/5 * * * * /mnt/seagate/scripts/tailscale_keepalive.sh') | crontab -",
    "echo 'Tailscale cron installed'",
]
for cmd in commands:
    stdin, stdout, stderr = ssh.exec_command(f"echo {SSH_PASS} | sudo -S sh -c \"{cmd}\"", timeout=10)
    out = stdout.read().decode().strip()
    if out:
        print(f"  {out}")

# Backup current gateway and restart
print("\n=== Backing up current gateway ===")
stdin, stdout, stderr = ssh.exec_command(
    f"cp -r {REMOTE_DIR} {REMOTE_DIR}.bak.$(date +%Y%m%d%H%M)", timeout=10
)
print("  Backup created")

# Restart gateway
print("\n=== Restarting ai-hub-gateway ===")
stdin, stdout, stderr = ssh.exec_command(
    f"echo {SSH_PASS} | sudo -S systemctl restart ai-hub-gateway", timeout=30
)
exit_status = stdout.channel.recv_exit_status()
print(f"  Restart exit: {exit_status}")

import time
print("  Waiting 8s for startup...")
time.sleep(8)

# Verify
print("\n=== Verifying ===")
checks = [
    ("Service", "systemctl is-active ai-hub-gateway"),
    ("Gateway HTTP", "curl -s -o /dev/null -w '%{http_code}' -m 5 http://localhost:9000/v1/status"),
    ("TTS", "curl -s -o /dev/null -w '%{http_code}' -m 10 http://localhost:9000/v1/audio/speech -H 'Content-Type: application/json' -d '{\"input\":\"Test\",\"voice\":\"es\"}'"),
]
for label, cmd in checks:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode().strip()
    print(f"  {label}: {out}")

# Check if watchdog is running
print("\n=== Watchdog check ===")
stdin, stdout, stderr = ssh.exec_command(
    "journalctl -u ai-hub-gateway --no-pager -n 20 2>&1 | grep -i watchdog", timeout=10
)
out = stdout.read().decode().strip()
print(f"  {'Watchdog started ✅' if 'watchdog' in out.lower() else 'Watchdog NOT found ❌'}")
if out:
    print(f"  Log: {out[:200]}")

ssh.close()
print("\n✅ Deploy complete!")
#!/usr/bin/env python3
"""Deploy Gateway + Studio updates to NAB9."""
import paramiko, sys, time, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd, timeout=120):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    return o.read().decode('utf-8','replace').strip(), e.read().decode('utf-8','replace').strip()

def upload(local, remote):
    # Create remote directory if needed
    remote_dir = os.path.dirname(remote).replace("\\", "/")
    run(f'mkdir -p "{remote_dir}"')
    sftp = ssh.open_sftp()
    sftp.put(local, remote)
    sftp.close()

# === 1. DEPLOY GATEWAY ===
print("=" * 50)
print("1. DEPLOYING GATEWAY")
print("=" * 50)

gateway_files = [
    ("ai-hub-gateway/main.py", "/mnt/seagate/ai-hub-gateway/main.py"),
    ("ai-hub-gateway/gateway/models/schemas.py", "/mnt/seagate/ai-hub-gateway/gateway/models/schemas.py"),
    ("ai-hub-gateway/gateway/routers/__init__.py", "/mnt/seagate/ai-hub-gateway/gateway/routers/__init__.py"),
    ("ai-hub-gateway/gateway/routers/voice.py", "/mnt/seagate/ai-hub-gateway/gateway/routers/voice.py"),
]

for local, remote in gateway_files:
    localpath = os.path.join(BASE, local.replace("/", os.sep))
    print(f"  Uploading {local}...")
    upload(localpath, remote)

# Restart gateway
print("  Restarting gateway service...")
run('echo pepe1234 | sudo -S systemctl restart ai-hub-gateway 2>/dev/null')
time.sleep(3)

# Check gateway
out, _ = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/ 2>/dev/null')
print(f"  Gateway :9000: {'ONLINE' if out == '200' else 'HTTP ' + out}")

# Test TTS endpoint exists
out, _ = run('curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/v1/audio/speech -H "Content-Type: application/json" -d \'{"input":"test"}\' 2>/dev/null')
print(f"  TTS endpoint /v1/audio/speech: {'OK' if out in ['200','422','502'] else 'HTTP ' + out}")

# === 2. DEPLOY AI HUB STUDIO ===
print("\n" + "=" * 50)
print("2. DEPLOYING AI HUB STUDIO")
print("=" * 50)

# Upload updated page.tsx
studio_file = os.path.join(BASE, "ai-hub-studio", "src", "app", "page.tsx")
print("  Uploading page.tsx...")
upload(studio_file, "/mnt/seagate/ai-hub-studio/src/app/page.tsx")

# Rebuild and deploy studio
print("  Building and deploying studio...")
out, err = run('cd /mnt/seagate/ai-hub-studio && python deploy.py 2>&1 | tail -5', timeout=300)
print(f"  {out}")

ssh.close()
print("\nDone!")
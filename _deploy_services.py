"""Deploy AI services (avatars + effects + TTS/STT) safely with VRAM monitoring."""
import paramiko
import socket
import time
import io

SERVER = "100.105.27.27"

# Read the service scripts
with open("_archive/avatar_services.py", "r", encoding="utf-8") as f:
    avatar_code = f.read()
with open("_archive/effects_services.py", "r", encoding="utf-8") as f:
    effects_code = f.read()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username="pepe", password="pepe1234", timeout=10)

def run(cmd, sudo=False):
    if sudo:
        cmd = f"echo pepe1234 | sudo -S {cmd}"
    _, o, e = ssh.exec_command(cmd, timeout=30)
    out = o.read().decode(errors="replace").strip()
    err = e.read().decode(errors="replace").strip()
    return out, err

def get_vram():
    out, _ = run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader 2>&1")
    return out

print("=" * 60)
print("  AI SERVICES DEPLOYMENT (Safe - with VRAM watchdog)")
print("=" * 60)
print()

# Step 1: Upload scripts
print("[1/5] Uploading service scripts...")
sftp = ssh.open_sftp()

# Create AI scripts directory
try:
    sftp.mkdir("/home/pepe/ai-scripts")
except:
    pass

sftp.putfo(io.BytesIO(avatar_code.encode("utf-8")), "/home/pepe/ai-scripts/avatar_services.py")
sftp.putfo(io.BytesIO(effects_code.encode("utf-8")), "/home/pepe/ai-scripts/effects_services.py")
print("  OK - avatar_services.py and effects_services.py uploaded")
sftp.close()
print()

# Step 2: Create systemd services
print("[2/5] Creating systemd service files...")

# Avatar service
avatar_svc = """[Unit]
Description=AI Hub Avatar Services (Hallo2, LatentSync, LivePortrait, MuseTalk)
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/pepe/ai-scripts/avatar_services.py
Restart=always
RestartSec=10
User=pepe
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

effects_svc = """[Unit]
Description=AI Hub Effects Services (Rembg, Upscale, Higgsfield)
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/pepe/ai-scripts/effects_services.py
Restart=always
RestartSec=10
User=pepe
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

sftp = ssh.open_sftp()
sftp.putfo(io.BytesIO(avatar_svc.encode()), "/tmp/ai-avatars.service")
sftp.putfo(io.BytesIO(effects_svc.encode()), "/tmp/ai-effects.service")
sftp.close()

run("cp /tmp/ai-avatars.service /etc/systemd/system/ai-avatars.service", sudo=True)
run("cp /tmp/ai-effects.service /etc/systemd/system/ai-effects.service", sudo=True)
run("systemctl daemon-reload", sudo=True)
print("  OK - Service files created")
print()

# Step 3: Check VRAM before starting
print("[3/5] VRAM before starting services:")
print(f"  {get_vram()}")
print()

# Step 4: Start services
print("[4/5] Starting services...")

# Start avatars
out, err = run("systemctl start ai-avatars", sudo=True)
print(f"  ai-avatars: started")
time.sleep(3)

# Start effects
out, err = run("systemctl start ai-effects", sudo=True)
print(f"  ai-effects: started")
time.sleep(3)

# Enable for boot
run("systemctl enable ai-avatars ai-effects", sudo=True)
print()

# Step 5: Verify all ports
print("[5/5] Verifying service ports...")
print()

services = [
    ("MuseTalk", 8040),
    ("LatentSync", 8043),
    ("LivePortrait", 8044),
    ("Hallo2", 8070),
    ("Rembg", 8050),
    ("Upscale", 8051),
    ("Higgsfield", 8052),
]

print(f"{'Service':<15} {'Port':<8} {'Status':<10}")
print("-" * 35)

for name, port in services:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    port_open = sock.connect_ex((SERVER, port)) == 0
    sock.close()
    status = "OPEN" if port_open else "CLOSED"
    print(f"{name:<15} {port:<8} {status:<10}")

# Final VRAM
print()
print("VRAM after starting services:")
print(f"  {get_vram()}")

# Service status
print()
print("Systemd status:")
out, _ = run("systemctl is-active ai-avatars ai-effects ai-hub-gateway ollama 2>&1")
print(f"  {out}")

ssh.close()
print()
print("=" * 60)
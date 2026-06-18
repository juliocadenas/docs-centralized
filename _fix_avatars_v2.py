"""Fix avatar services: install deps and restart."""
import paramiko
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=30)

def run(cmd, sudo=False):
    if sudo:
        cmd = f"echo pepe1234 | sudo -S {cmd}"
    _, o, e = ssh.exec_command(cmd, timeout=120)
    return o.read().decode(errors="replace").strip(), e.read().decode(errors="replace").strip()

print("[1/3] Installing uvicorn + fastapi...")
out, err = run("pip3 install uvicorn fastapi 2>&1", sudo=True)
# Show last few lines
for line in out.split("\n")[-5:]:
    print(f"  {line}")
print()

print("[2/3] Verifying deps...")
out, _ = run("python3 -c 'import uvicorn; print(f\"uvicorn {uvicorn.__version__}\")' 2>&1")
print(f"  {out}")
out, _ = run("python3 -c 'import fastapi; print(f\"fastapi {fastapi.__version__}\")' 2>&1")
print(f"  {out}")
print()

print("[3/3] Restarting avatar service...")
out, _ = run("systemctl restart ai-avatars 2>&1", sudo=True)
print(f"  Restarted")

import time
time.sleep(5)

out, _ = run("systemctl is-active ai-avatars 2>&1")
print(f"  Status: {out}")

# Check ports
import socket
ports = [8040, 8043, 8044, 8070]
print()
print("Avatar ports:")
for port in ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    open_ = sock.connect_ex(("100.105.27.27", port)) == 0
    sock.close()
    print(f"  {port}: {'OPEN' if open_ else 'CLOSED'}")

ssh.close()
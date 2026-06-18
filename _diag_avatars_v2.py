"""Check avatars service logs."""
import paramiko
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=30)

def run(cmd):
    _, o, _ = ssh.exec_command(cmd, timeout=15)
    return o.read().decode(errors="replace").strip()

print("=== AVATAR SERVICE STATUS ===")
print(run("systemctl status ai-avatars 2>&1 | head -20"))
print()
print("=== AVATAR SERVICE LOGS ===")
print(run("journalctl -u ai-avatars --no-pager -n 20 2>&1"))
print()
print("=== CHECK DEPS ===")
print(run("python3 -c 'import uvicorn; print(uvicorn.__version__)' 2>&1"))
print(run("python3 -c 'import fastapi; print(fastapi.__version__)' 2>&1"))

ssh.close()
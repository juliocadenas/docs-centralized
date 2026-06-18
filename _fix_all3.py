"""Discover TTS endpoints + restart services + re-test."""
import os
import sys
import time

try:
    import paramiko
except ImportError:
    os.system(f"{sys.executable} -m pip install paramiko -q")
    import paramiko

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=60):
    print(f"\n>>> {cmd[:120]}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out[:1200])
    if err and "[sudo]" not in err:
        print(f"  ERR: {err[:300]}")
    return out

# 1. Discover TTS endpoints
print("=== 1. TTS API discovery ===")
run("curl -s http://localhost:8010/openapi.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(json.dumps(list(d['paths'].keys())))\" 2>&1")

# 2. Check effects service is working after restart
print("\n=== 2. Effects health ===")
run("curl -s http://localhost:8050/health 2>&1")
run("curl -s http://localhost:8051/health 2>&1")

# 3. Kill the bloated STT process and restart it
print("\n=== 3. Restart STT ===")
run(f"echo '{PASS}' | sudo -S systemctl list-units | grep -i stt 2>&1")
# Check if STT has its own service
run(f"echo '{PASS}' | sudo -S systemctl list-units | grep -i whisper 2>&1")

# 4. Free VRAM by killing unused avatar services
print("\n=== 4. GPU before cleanup ===")
run("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>&1")

# Check all services
run(f"echo '{PASS}' | sudo -S systemctl list-units --type=service --state=running | grep -iE 'ai|avatar|muse|latent|live|hallo' 2>&1")

# 5. Restart STT to retry model loading
print("\n=== 5. Restart STT service ===")
# Try to find STT service name
run("systemctl list-units --type=service | grep -i stt 2>&1 || echo 'no stt service'")
# Check if it runs under a different name
run("ps aux | grep stt_svc | grep -v grep")

ssh.close()
print("\n[DONE]")
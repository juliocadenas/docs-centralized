"""
Diagnostico completo del servidor Madrid via SSH.
Verifica Docker, servicios, puertos y GPU.
"""
import os
import sys

try:
    import paramiko
except ImportError:
    os.system(f"{sys.executable} -m pip install paramiko -q")
    import paramiko

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

COMMANDS = [
    ("Docker containers", "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>&1"),
    ("Docker images", "docker images --format '{{.Repository}}:{{.Tag}}' 2>&1 | head -20"),
    ("Ports listening", "ss -tlnp 2>/dev/null | grep -E ':(80[0-9]{2}|81[0-9]{2}|90[0-9]{2}|30[0-9]{2}|11[0-9]{3})' | sort"),
    ("Systemd AI services", "systemctl list-units --type=service | grep -iE 'ai-hub|comfy|ollama|wan|docu|muse|piper|whisper|rembg|upscale|effects' 2>&1"),
    ("GPU status", "nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1"),
    ("Gateway logs (last 10)", f"echo '{PASS}' | sudo -S journalctl -u ai-hub-gateway --no-pager -n 10 2>&1"),
    ("Rembg service check", "curl -s -o /dev/null -w '%{http_code}' http://localhost:8050/ 2>&1 || echo 'NOT RUNNING'"),
    ("Upscale service check", "curl -s -o /dev/null -w '%{http_code}' http://localhost:8051/ 2>&1 || echo 'NOT RUNNING'"),
    ("Piper TTS check", "curl -s -o /dev/null -w '%{http_code}' http://localhost:8010/ 2>&1 || echo 'NOT RUNNING'"),
    ("Whisper STT check", "curl -s -o /dev/null -w '%{http_code}' http://localhost:8011/ 2>&1 || echo 'NOT RUNNING'"),
]

def main():
    print(f"[INFO] Connecting to {USER}@{HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    print("[OK] Connected!\n")

    for title, cmd in COMMANDS:
        print(f"=== {title} ===")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if output:
            print(output)
        if err and "Warning" not in err:
            print(f"  [stderr] {err[:200]}")
        print()

    ssh.close()
    print("[DONE] Diagnostic complete!")


if __name__ == "__main__":
    main()
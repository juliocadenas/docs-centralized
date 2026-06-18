"""Fix backend models: RealESRGAN, Whisper, check TTS."""
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

commands = [
    # 1. Check what's running
    "echo '=== Running services ===' && curl -s http://localhost:8010/ | head -c 200 && echo",
    "echo '=== TTS logs (last 5) ===' && echo 'pepe1234' | sudo -S journalctl -u piper-tts --no-pager -n 5 2>&1 | tail -5",
    
    # 2. Check Whisper STT model
    "echo '=== Whisper model status ===' && curl -s http://localhost:8020/api/status 2>&1",
    "ls -la /mnt/seagate/models/whisper/ 2>/dev/null || echo 'No whisper dir'",
    "find /mnt/seagate/models -name '*whisper*' -o -name '*Whisper*' 2>/dev/null | head -10",
    
    # 3. Check RealESRGAN model
    "echo '=== RealESRGAN model ===' && ls -la /home/pepe/.cache/realesrgan/ 2>/dev/null || echo 'No realesrgan cache'",
    "find /mnt/seagate/models -name '*RealESRGAN*' -o -name '*realesrgan*' -o -name '*ESRGAN*' 2>/dev/null | head -10",
    
    # 4. Check GPU state
    "echo '=== GPU ===' && nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>&1",
    
    # 5. List running docker/processes
    "echo '=== Processes ===' && ps aux | grep -E 'piper|whisper|rembg|realesrgan|8010|8020|8050|8051' | grep -v grep",
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)

for cmd in commands:
    print(f"\n>>> {cmd[:80]}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out[:500])
    if err:
        print(f"  STDERR: {err[:200]}")

ssh.close()
print("\n[DONE]")
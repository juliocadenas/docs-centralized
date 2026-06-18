import paramiko, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

SCRIPT = r'''
import os, sys
from huggingface_hub import snapshot_download

MODELS = [
    ("fudan-generative-ai/hallo2", "/mnt/seagate/models/hallo2"),
    ("ByteDance/LatentSync", "/mnt/seagate/models/latentsync"),
    ("KwaiVGI/LivePortrait", "/mnt/seagate/models/liveportrait"),
    ("TMElyralab/MuseTalk", "/mnt/seagate/models/musetalk"),
]

for repo, local in MODELS:
    print(f"Downloading {repo} -> {local}")
    try:
        snapshot_download(repo, local_dir=local, resume_download=True)
        print(f"OK: {repo}")
    except Exception as e:
        print(f"ERROR {repo}: {e}")

print("DONE - All downloads attempted")
'''

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=20)
    
    # Write script
    print("Uploading script...")
    stdin, stdout, stderr = c.exec_command(f"cat > /tmp/download_ckpts.py << 'EOF'\n{SCRIPT}\nEOF", timeout=10)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if err: print("WRITE ERR:", err[:200])
    
    # Run downloads (this will take a while)
    print("Starting downloads (may take 30+ min)...")
    stdin, stdout, stderr = c.exec_command("cd /mnt/seagate && nohup /home/pepe/comfyui_env/bin/python3 /tmp/download_ckpts.py > /tmp/download_ckpts.log 2>&1 & echo PID=$!", timeout=10)
    pid = stdout.read().decode().strip()
    print(f"Download PID: {pid}")
    
    time.sleep(5)
    
    # Check initial progress
    stdin, stdout, stderr = c.exec_command("head -10 /tmp/download_ckpts.log 2>/dev/null", timeout=5)
    log = stdout.read().decode().strip()
    if log: print("Initial log:", log[:400])
    
    c.close()
    print("Downloads running in background on NAB9")

if __name__ == "__main__":
    main()
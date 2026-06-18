#!/usr/bin/env python3
"""Download MuseTalk models with correct venv paths."""
import paramiko, sys, time, socket
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def ssh_run(cmd, timeout=300, retries=2):
    for attempt in range(retries):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=8)
            chan = ssh.get_transport().open_session()
            chan.exec_command(cmd)
            chan.settimeout(timeout)
            try:
                out = chan.makefile('r', -1).read().strip()
                if isinstance(out, bytes):
                    out = out.decode('utf-8', errors='replace')
            except socket.timeout:
                out = "(timeout)"
            chan.close()
            ssh.close()
            return out
        except Exception as e:
            try: ssh.close()
            except: pass
            if attempt < retries - 1:
                time.sleep(3)
            return f"(SSH FAILED: {e})"

PIP = "/home/pepe/ai_env/bin/pip"
PYTHON = "/home/pepe/ai_env/bin/python"
HF_CLI = "/home/pepe/ai_env/bin/huggingface-cli"
GDOWN = "/home/pepe/ai_env/bin/gdown"
MODELS_DIR = "/mnt/seagate/MuseTalk/models"

# Step 1: Install huggingface_hub[cli]
print("=== Install huggingface_hub[cli] ===")
print(ssh_run(f"{PIP} install -U 'huggingface_hub[cli]' 2>&1 | tail -5", timeout=120))

# Step 2: Create dirs
print("\n=== Create model dirs ===")
dirs = " ".join([
    f"{MODELS_DIR}/musetalk", f"{MODELS_DIR}/musetalkV15",
    f"{MODELS_DIR}/syncnet", f"{MODELS_DIR}/dwpose",
    f"{MODELS_DIR}/face-parse-bisent", f"{MODELS_DIR}/sd-vae",
    f"{MODELS_DIR}/whisper"
])
print(ssh_run(f"mkdir -p {dirs} 2>&1"))

# Step 3: Download MuseTalk weights from HuggingFace
print("\n=== Download MuseTalk from HuggingFace ===")
print(ssh_run(
    f"export HF_ENDPOINT=https://hf-mirror.com && "
    f"{HF_CLI} download TMElyralab/MuseTalk "
    f"--local-dir {MODELS_DIR} "
    f"--include 'musetalk/musetalk.json' 'musetalk/pytorch_model.bin' 2>&1 | tail -10",
    timeout=180
))

# Step 4: Download MuseTalk V1.5
print("\n=== Download MuseTalk V1.5 ===")
print(ssh_run(
    f"export HF_ENDPOINT=https://hf-mirror.com && "
    f"{HF_CLI} download TMElyralab/MuseTalk "
    f"--local-dir {MODELS_DIR} "
    f"--include 'musetalkV15/musetalkV15.json' 'musetalkV15/pytorch_model.bin' 2>&1 | tail -10",
    timeout=180
))

# Step 5: Download SD VAE
print("\n=== Download SD VAE ===")
print(ssh_run(
    f"export HF_ENDPOINT=https://hf-mirror.com && "
    f"{HF_CLI} download stabilityai/sd-vae-ft-mse "
    f"--local-dir {MODELS_DIR}/sd-vae "
    f"--include 'diffusion_pytorch_model.bin' 'config.json' 2>&1 | tail -10",
    timeout=120
))

# Step 6: Download Whisper
print("\n=== Download Whisper ===")
print(ssh_run(
    f"export HF_ENDPOINT=https://hf-mirror.com && "
    f"{HF_CLI} download openai/whisper-tiny "
    f"--local-dir {MODELS_DIR}/whisper "
    f"--include 'pytorch_model.bin' 'config.json' 2>&1 | tail -10",
    timeout=120
))

# Step 7: Download SyncNet, DWPose, FaceParse from gdrive
print("\n=== Download SyncNet (gdown) ===")
print(ssh_run(
    f"{GDOWN} 1yYU8GlmH5gJZ7XJc83dwm2zr4Wx2NtsJ -O {MODELS_DIR}/syncnet.zip 2>&1 | tail -5",
    timeout=120
))
print(ssh_run(f"cd {MODELS_DIR}/syncnet && unzip -o ../syncnet.zip 2>&1 | tail -5"))

print("\n=== Download DWPose (gdown) ===")
print(ssh_run(
    f"{GDOWN} 1I3K2Opy7fLzL8m4XjJXK2QQ7K0Z3j6oA -O {MODELS_DIR}/dwpose.zip 2>&1 | tail -5",
    timeout=120
))
print(ssh_run(f"cd {MODELS_DIR}/dwpose && unzip -o ../dwpose.zip 2>&1 | tail -5"))

print("\n=== Download FaceParse (gdown) ===")
print(ssh_run(
    f"{GDOWN} 1f7O6Z9r8XjZ0m8m6m9c3wZ6N3Yr8XjZ0 -O {MODELS_DIR}/face-parse-bisent.zip 2>&1 | tail -5",
    timeout=120
))

# Check what we got
print("\n=== Models downloaded ===")
print(ssh_run(f"find {MODELS_DIR} -name '*.bin' -o -name '*.pth' -o -name '*.json' 2>&1 | head -30"))

# Relaunch MuseTalk
print("\n=== Relaunch MuseTalk ===")
print(ssh_run("fuser -k 8040/tcp 2>/dev/null; sleep 2; echo killed"))
launch_cmd = (
    f"cd /mnt/seagate/MuseTalk && "
    f"nohup {PYTHON} app.py "
    f"--server_port 8040 --server_name 0.0.0.0 "
    f"> /tmp/musetalk.log 2>&1 &"
)
print(ssh_run(launch_cmd, timeout=5))
time.sleep(25)

print("MuseTalk log (last 20):")
print(ssh_run("tail -20 /tmp/musetalk.log 2>&1"))

print("\n=== All ports ===")
for p in [8040, 8043, 8044, 8070]:
    r = ssh_run(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{p}/ --connect-timeout 3 2>&1')
    print(f"  :{p}: HTTP {r}")

print("\nDONE")
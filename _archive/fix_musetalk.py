#!/usr/bin/env python3
"""Download MuseTalk models via Python huggingface_hub."""
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

PYTHON = "/home/pepe/ai_env/bin/python"
MODELS_DIR = "/mnt/seagate/MuseTalk/models"

# Read the full download script first
print("=== Full download script ===")
print(ssh_run("cat /mnt/seagate/MuseTalk/download_weights.sh 2>&1"))

# Download via Python huggingface_hub API
print("\n=== Download MuseTalk weights ===")
print(ssh_run(
    f'export HF_ENDPOINT=https://hf-mirror.com && '
    f'{PYTHON} -c "'
    f'from huggingface_hub import snapshot_download;'
    f'snapshot_download(\\"TMElyralab/MuseTalk\\", '
    f'allow_patterns=[\\"musetalk/*\\", \\"musetalkV15/*\\"], '
    f'local_dir=\\"{MODELS_DIR}\\");'
    f'print(\\"MuseTalk weights downloaded\\")'
    f'" 2>&1 | tail -5',
    timeout=180
))

# SD VAE
print("\n=== Download SD VAE ===")
print(ssh_run(
    f'export HF_ENDPOINT=https://hf-mirror.com && '
    f'{PYTHON} -c "'
    f'from huggingface_hub import snapshot_download;'
    f'snapshot_download(\\"stabilityai/sd-vae-ft-mse\\", '
    f'allow_patterns=[\\"*.bin\\", \\"*.json\\"], '
    f'local_dir=\\"{MODELS_DIR}/sd-vae\\");'
    f'print(\\"SD VAE downloaded\\")'
    f'" 2>&1 | tail -5',
    timeout=120
))

# Whisper tiny
print("\n=== Download Whisper ===")
print(ssh_run(
    f'export HF_ENDPOINT=https://hf-mirror.com && '
    f'{PYTHON} -c "'
    f'from huggingface_hub import snapshot_download;'
    f'snapshot_download(\\"openai/whisper-tiny\\", '
    f'allow_patterns=[\\"*.bin\\", \\"*.json\\"], '
    f'local_dir=\\"{MODELS_DIR}/whisper\\");'
    f'print(\\"Whisper downloaded\\")'
    f'" 2>&1 | tail -5',
    timeout=120
))

# Check existing models in /mnt/seagate/models
print("\n=== Existing musetalk models ===")
print(ssh_run("ls -la /mnt/seagate/models/musetalk/musetalk/ 2>&1"))
print(ssh_run("ls -la /mnt/seagate/models/musetalk/musetalkV15/ 2>&1"))

# Check what we got
print("\n=== Models downloaded ===")
print(ssh_run(f"find {MODELS_DIR} -type f 2>&1 | head -30"))

print("\nDONE")
#!/usr/bin/env python3
"""Download MuseTalk models without HF mirror."""
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

print("=== Download SD VAE ===")
print(ssh_run(
    f'{PYTHON} -c "'
    f'from huggingface_hub import snapshot_download;'
    f'snapshot_download(\\"stabilityai/sd-vae-ft-mse\\", '
    f'allow_patterns=[\\"diffusion_pytorch_model.bin\\", \\"config.json\\"], '
    f'local_dir=\\"/mnt/seagate/MuseTalk/models/sd-vae\\");'
    f'print(\\"SD VAE OK\\")'
    f'" 2>&1 | tail -5',
    timeout=120
))

print("\n=== Download Whisper ===")
print(ssh_run(
    f'{PYTHON} -c "'
    f'from huggingface_hub import snapshot_download;'
    f'snapshot_download(\\"openai/whisper-tiny\\", '
    f'allow_patterns=[\\"pytorch_model.bin\\", \\"config.json\\", \\"preprocessor_config.json\\"], '
    f'local_dir=\\"/mnt/seagate/MuseTalk/models/whisper\\");'
    f'print(\\"Whisper OK\\")'
    f'" 2>&1 | tail -5',
    timeout=120
))

print("\n=== Download DWPose ===")
print(ssh_run(
    f'{PYTHON} -c "'
    f'from huggingface_hub import hf_hub_download;'
    f'hf_hub_download(\\"yzd-v/DWPose\\", \\"dw-ll_ucoco_384.pth\\", '
    f'local_dir=\\"/mnt/seagate/MuseTalk/models/dwpose\\");'
    f'print(\\"DWPose OK\\")'
    f'" 2>&1 | tail -5',
    timeout=120
))

print("\n=== Download SyncNet ===")
print(ssh_run(
    f'{PYTHON} -c "'
    f'from huggingface_hub import hf_hub_download;'
    f'hf_hub_download(\\"ByteDance/LatentSync\\", \\"latentsync_syncnet.pt\\", '
    f'local_dir=\\"/mnt/seagate/MuseTalk/models/syncnet\\");'
    f'print(\\"SyncNet OK\\")'
    f'" 2>&1 | tail -5',
    timeout=120
))

print("\n=== Download FaceParse ===")
print(ssh_run(
    f'/home/pepe/ai_env/bin/gdown --id 154JgKpzCPW82qINcVieuPH3fZ2e0P812 '
    f'-O /mnt/seagate/MuseTalk/models/face-parse-bisent/79999_iter.pth 2>&1 | tail -5',
    timeout=120
))

print("\n=== Download ResNet18 ===")
print(ssh_run(
    f'curl -L https://download.pytorch.org/models/resnet18-5c106cde.pth '
    f'-o /mnt/seagate/MuseTalk/models/face-parse-bisent/resnet18-5c106cde.pth 2>&1 | tail -5',
    timeout=60
))

print("\n=== All models ===")
print(ssh_run("find /mnt/seagate/MuseTalk/models -type f \\( -name '*.bin' -o -name '*.pth' -o -name '*.pt' -o -name '*.json' \\) 2>&1"))

print("\n=== Relaunch MuseTalk ===")
print(ssh_run("fuser -k 8040/tcp 2>/dev/null; sleep 2; echo killed"))
print(ssh_run(
    f"cd /mnt/seagate/MuseTalk && nohup {PYTHON} app.py --server_port 8040 --server_name 0.0.0.0 > /tmp/musetalk.log 2>&1 &",
    timeout=5
))
time.sleep(25)
print("MuseTalk log:")
print(ssh_run("tail -20 /tmp/musetalk.log 2>&1"))

print("\n=== Ports ===")
for p in [8040, 8043, 8044, 8070]:
    r = ssh_run(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{p}/ --connect-timeout 3 2>&1')
    print(f"  :{p}: HTTP {r}")

print("\nDONE")
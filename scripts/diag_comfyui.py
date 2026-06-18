#!/usr/bin/env python3
"""Fix ComfyUI: check checkpoints and test directly."""
import requests, sys, paramiko, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. Check ComfyUI checkpoints directly
print("=== ComfyUI checkpoints ===")
r = requests.get("http://100.105.27.27:8188/object_info/CheckpointLoaderSimple", timeout=10)
if r.status_code == 200:
    data = r.json()
    ckpts = data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])
    if ckpts and len(ckpts) > 0:
        print(f"Available checkpoints: {ckpts[0]}")
    else:
        print("No checkpoints found!")
else:
    print(f"HTTP {r.status_code}")

# 2. Check disk
print("\n=== Check models directory ===")
s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=30)

_, o, e = s.exec_command('find /mnt/seagate/comfyui/models/checkpoints/ -type f 2>/dev/null; echo "---"; ls -la /mnt/seagate/comfyui/models/checkpoints/ 2>/dev/null; echo "---"; find /mnt/seagate/models/sd/ -type f 2>/dev/null | head -10')
print(o.read().decode(errors='replace'))

# 3. comfyui service config
_, o, _ = s.exec_command('cat /etc/systemd/system/comfyui.service')
print("\n=== comfyui.service ===")
print(o.read().decode(errors='replace'))

# 4. Read workflow builder
_, o, _ = s.exec_command('grep -B 2 -A 50 "def _build_txt2img_workflow" /mnt/seagate/ai-hub-gateway/gateway/services/comfyui.py')
print("\n=== workflow builder ===")
print(o.read().decode(errors='replace'))

s.close()
"""Check ai_env torch + create systemd services for all avatar/effects."""
import paramiko, time, textwrap

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=120):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:500] if err else "")

# 1. Check ai_env torch
print("=== ai_env torch ===")
print(run('/home/pepe/ai_env/bin/python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else \'NO CUDA\')" 2>&1'))

# 2. Check what apps exist
print("\n=== App scripts in /home/pepe ===")
print(run("ls -la /home/pepe/*app.py /home/pepe/serve_avatars.py /home/pepe/effects_service*.py 2>&1"))

# 3. Check how LivePortrait app.py works
print("\n=== LivePortrait app.py header ===")
print(run("head -20 /mnt/seagate/LivePortrait/app.py 2>&1"))

# 4. Check MuseTalk app.py
print("\n=== MuseTalk app.py header ===")
print(run("head -20 /mnt/seagate/MuseTalk/app.py 2>&1"))

# 5. Check LatentSync structure
print("\n=== LatentSync structure ===")
print(run("ls /mnt/seagate/LatentSync/*.py 2>&1"))

# 6. Check Hallo2 structure
print("\n=== Hallo2 structure ===")
print(run("ls /mnt/seagate/hallo2/*.py /home/pepe/hallo2_app.py 2>&1"))

# 7. Check current VRAM
print("\n=== nvidia-smi ===")
print(run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader 2>&1"))

s.close()
print("\nDone!")
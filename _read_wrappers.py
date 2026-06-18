"""Read the wrapper scripts and create systemd services."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=60):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:300] if err else "")

# Read all wrapper scripts
for script in ["musetalk_app.py", "latentsync_app.py", "liveportrait_app.py", "hallo2_app.py"]:
    print(f"\n{'='*50}")
    print(f"  {script}")
    print(f"{'='*50}")
    print(run(f"cat /home/pepe/{script} 2>&1"))

# Check effects_service_real.py
print(f"\n{'='*50}")
print("  effects_service_real.py (running process)")
print(f"{'='*50}")
print(run("head -40 /home/pepe/effects_service_real.py 2>&1"))

# Check LatentSync gradio_app.py
print(f"\n{'='*50}")
print("  LatentSync gradio_app.py")
print(f"{'='*50}")
print(run("head -25 /mnt/seagate/LatentSync/gradio_app.py 2>&1"))

# Check MuseTalk app.py launch
print(f"\n{'='*50}")
print("  MuseTalk launch.py")
print(f"{'='*50}")
print(run("ls /mnt/seagate/MuseTalk/app.py /mnt/seagate/MuseTalk/entry.py 2>&1"))

# Check Hallo2 real location
print(f"\n{'='*50}")
print("  Hallo2 location")
print(f"{'='*50}")
print(run("ls -la /mnt/seagate/hallo2/ 2>&1 | head -15"))
print(run("find /mnt/seagate -maxdepth 2 -name 'hallo*' -type d 2>&1"))

s.close()
print("\nDone!")
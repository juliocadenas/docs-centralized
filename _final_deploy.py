"""Final deploy: upload gpu_manager.py, fix MuseTalk numpy, restart all."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=300):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:400] if err else "")

def write_remote(path, content):
    sftp = s.open_sftp()
    with sftp.open(path, 'w') as f:
        f.write(content)
    sftp.close()

# ============================================================
# 1. Upload updated gpu_manager.py
# ============================================================
print("=== Upload gpu_manager.py ===")
with open(r"c:\Users\julio\Documents\Proyectos\IA-HUB-MADRID1\ai-hub-gateway\gateway\gpu_manager.py", "r") as f:
    write_remote("/mnt/seagate/ai-hub-gateway/gateway/gpu_manager.py", f.read())
print("  OK")

# ============================================================
# 2. Fix MuseTalk: xtcocotools needs numpy < 2.0
#    The C extension was compiled against numpy 1.x
# ============================================================
print("\n=== Fix MuseTalk numpy ===")
# Check current numpy
print(run("/home/pepe/ai_env/bin/python -c 'import numpy; print(numpy.__version__)' 2>&1"))

# Downgrade numpy to 1.26 (last 1.x - compatible with xtcocotools C ext)
print("  Downgrading numpy to 1.26.4...")
print(run("/home/pepe/ai_env/bin/pip install 'numpy<2.0' 2>&1 | tail -5", 300))

# Reinstall xtcocotools fresh
print("  Reinstalling xtcocotools...")
print(run("/home/pepe/ai_env/bin/pip install --force-reinstall --no-deps xtcocotools 2>&1 | tail -3", 120))

# Verify
print("  Verify:")
print(run("/home/pepe/ai_env/bin/python -c 'from xtcocotools.coco import COCO; print(\"xtcocotools OK\")' 2>&1"))

# ============================================================
# 3. Restart MuseTalk
# ============================================================
print("\n=== Restart MuseTalk ===")
run("echo pepe1234 | sudo -S systemctl restart musetalk 2>&1")
time.sleep(20)
print(f"  MuseTalk: {run('systemctl is-active musetalk 2>&1')}")

# ============================================================
# 4. Restart Gateway with updated health checks
# ============================================================
print("\n=== Restart Gateway ===")
run("echo pepe1234 | sudo -S systemctl restart ai-hub-gateway 2>&1")
time.sleep(8)
print(f"  Gateway: {run('systemctl is-active ai-hub-gateway 2>&1')}")

# ============================================================
# 5. Wait a bit and check final status
# ============================================================
time.sleep(10)
print("\n=== Final Status ===")
status_raw = run("curl -s http://localhost:9000/v1/status")
if status_raw:
    import json
    try:
        d = json.loads(status_raw)
        online = sum(1 for sv in d.get("services", []) if sv.get("status") == "online")
        total = len(d.get("services", []))
        print(f"  Online: {online}/{total}")
        for sv in d.get("services", []):
            mark = "OK" if sv.get("status") == "online" else "XX"
            print(f"    [{mark}] {sv.get('name','?'):30s} {sv.get('status','?'):10s} :{sv.get('port','?')}")
    except Exception as ex:
        print(f"  Error: {ex}")
        print(f"  RAW: {status_raw[:300]}")

# VRAM
print(f"\n=== VRAM ===")
print(run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader"))

s.close()
print("\nDone!")
"""Fix MuseTalk xtcocotools from source + check Gateway health for LivePortrait."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=300):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:400] if err else "")

# ============================================================
# 1. Fix xtcocotools - rebuild from source against numpy 2.4.6
# ============================================================
print("=== Rebuild xtcocotools from source ===")
print(run("/home/pepe/ai_env/bin/pip uninstall -y xtcocotools 2>&1 | tail -2"))
# Install cython first
print(run("/home/pepe/ai_env/bin/pip install cython 2>&1 | tail -2"))
# Install from source to rebuild C extension
print(run("/home/pepe/ai_env/bin/pip install xtcocotools --no-binary :all: --no-build-isolation 2>&1 | tail -10", 300))

# Verify
print("\n=== Verify xtcocotools ===")
print(run("/home/pepe/ai_env/bin/python -c 'from xtcocotools.coco import COCO; print(\"xtcocotools OK\")' 2>&1"))

# ============================================================
# 2. Also try mmpycocotools if needed
# ============================================================
print("\n=== Check mmpycocotools ===")
print(run("/home/pepe/ai_env/bin/pip install --force-reinstall --no-deps mmpycocotools 2>&1 | tail -3", 120))

# ============================================================
# 3. Restart MuseTalk
# ============================================================
print("\n=== Restart MuseTalk ===")
run("echo pepe1234 | sudo -S systemctl restart musetalk 2>&1")
time.sleep(20)
mt = run("systemctl is-active musetalk 2>&1")
print(f"MuseTalk: {mt}")
if "active" not in mt:
    print(run("journalctl -u musetalk --no-pager -n 5 2>&1"))

# ============================================================
# 4. Check LivePortrait and LatentSync ports directly
# ============================================================
print("\n=== Port checks ===")
for port, name in [(8041, "MuseTalk"), (8043, "LatentSync"), (8044, "LivePortrait"), (8070, "Hallo2")]:
    code = run("curl -s -o /dev/null -w " + chr(39) + "%{http_code}" + chr(39) + " --max-time 10 http://localhost:" + str(port) + "/ 2>&1")
    print(f"  :{port} {name}: {code}")

# ============================================================
# 5. Restart Gateway to refresh health checks
# ============================================================
print("\n=== Restart Gateway ===")
run("echo pepe1234 | sudo -S systemctl restart ai-hub-gateway 2>&1")
time.sleep(8)

# ============================================================
# 6. Final status
# ============================================================
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

s.close()
print("\nDone!")
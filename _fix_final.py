"""Fix effects systemd + LivePortrait crash-loop + start Hallo2."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=120):
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
# 1. Fix Effects systemd - point to correct script
# ============================================================
print("=== Fix Effects systemd ===")
effects_svc = """[Unit]
Description=Effects Services (Rembg + Real-ESRGAN)
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/mnt/seagate/ai-hub-gateway
ExecStart=/home/pepe/ai_env/bin/python effects_service_real.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
write_remote("/tmp/effects.service", effects_svc)
print(run("echo pepe1234 | sudo -S cp /tmp/effects.service /etc/systemd/system/effects.service 2>&1"))
print(run("echo pepe1234 | sudo -S systemctl daemon-reload 2>&1"))

# Kill old effects process and start via systemd
print("  Killing old process 1687561...")
run("kill 1687561 2>&1")
time.sleep(3)
print(run("echo pepe1234 | sudo -S systemctl start effects 2>&1"))
time.sleep(10)
print(f"  Effects: {run('systemctl is-active effects 2>&1')}")

# ============================================================
# 2. Stop LivePortrait crash-loop - it keeps failing
#    The old process is still serving on 8044
# ============================================================
print("\n=== Stop LivePortrait crash-loop ===")
# Check if port 8044 still works
lp_code = run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8044/ 2>&1")
print(f"  Port 8044: {lp_code}")
if lp_code == "200":
    print("  Port works! Stop systemd to avoid crash-loop")
    run("echo pepe1234 | sudo -S systemctl stop liveportrait 2>&1")
    run("echo pepe1234 | sudo -S systemctl disable liveportrait 2>&1")
    print("  Stopped systemd, old process still serving")
else:
    # Check error
    print(run("journalctl -u liveportrait --no-pager -n 15 2>&1"))

# ============================================================
# 3. Start Hallo2
# ============================================================
print("\n=== Start Hallo2 ===")
print(run("echo pepe1234 | sudo -S systemctl start hallo2 2>&1"))
time.sleep(15)
h2 = run("systemctl is-active hallo2 2>&1")
print(f"  Hallo2: {h2}")
if "active" not in h2:
    print(run("journalctl -u hallo2 --no-pager -n 10 2>&1"))
    run("echo pepe1234 | sudo -S systemctl stop hallo2 2>&1")

# ============================================================
# 4. Final status via Gateway API
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
        print(f"  Parse error: {ex}")
        print(f"  RAW: {status_raw[:300]}")

# VRAM
print(f"\n=== VRAM ===")
print(run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader"))

s.close()
print("\nDone!")
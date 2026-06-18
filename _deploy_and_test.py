"""Deploy updated gateway + enable systemd services + test endpoints."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=120):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:300] if err else "")

def write_remote(path, content):
    sftp = s.open_sftp()
    with sftp.open(path, 'w') as f:
        f.write(content)
    sftp.close()

# 1. Upload config.py
print("=== Upload config.py ===")
with open(r"c:\Users\julio\Documents\Proyectos\IA-HUB-MADRID1\ai-hub-gateway\gateway\config.py", "r") as f:
    write_remote("/mnt/seagate/ai-hub-gateway/gateway/config.py", f.read())
print("  OK")

# 2. Enable services
print("\n=== Enable systemd services ===")
for svc in ["musetalk", "latentsync", "liveportrait", "hallo2", "effects"]:
    r = run("echo pepe1234 | sudo -S systemctl enable " + svc + " 2>&1")
    print(f"  {svc}: {r}")

# 3. Restart Gateway
print("\n=== Restart Gateway ===")
run("echo pepe1234 | sudo -S systemctl restart ai-hub-gateway 2>&1")
time.sleep(5)
gw = run("systemctl is-active ai-hub-gateway 2>&1")
print(f"Gateway: {gw}")

# 4. Test endpoints
print("\n=== Test Endpoints ===")
s1 = run("curl -s -o /dev/null -w " + chr(39) + "%{http_code}" + chr(39) + " http://localhost:9000/v1/status")
s2 = run("curl -s -o /dev/null -w " + chr(39) + "%{http_code}" + chr(39) + " http://localhost:9000/v1/models")
s3 = run("curl -s -o /dev/null -w " + chr(39) + "%{http_code}" + chr(39) + " http://localhost:9000/v1/infrastructure")
print(f"  /v1/status: {s1}")
print(f"  /v1/models: {s2}")
print(f"  /v1/infrastructure: {s3}")

# 5. Count services online
print("\n=== Service Count ===")
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
    except:
        print(f"  RAW: {status_raw[:200]}")

# VRAM
print(f"\n=== VRAM ===")
print(run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader"))

s.close()
print("\nDone!")
"""Configure proper VRAM management: disable heavy services auto-start, keep essentials."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=60):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:400] if err else "")

# Stop heavy services
print("=== Stop heavy services ===")
for svc in ["musetalk", "latentsync", "liveportrait", "hallo2", "effects"]:
    run("echo pepe1234 | sudo -S systemctl stop " + svc + " 2>&1")
    print(f"  {svc}: stopped")

# Kill orphan processes
run("fuser -k 8044/tcp 2>&1")
run("fuser -k 8041/tcp 2>&1")
run("fuser -k 8043/tcp 2>&1")
time.sleep(3)
print("Killed orphans")

# Check VRAM
print("\n=== VRAM after cleanup ===")
print(run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader"))

# Test MuseTalk alone
print("\n=== Test MuseTalk alone ===")
run("echo pepe1234 | sudo -S systemctl start musetalk 2>&1")
time.sleep(25)
mt = run("systemctl is-active musetalk 2>&1")
print(f"  MuseTalk: {mt}")
if "active" not in mt:
    print(run("journalctl -u musetalk --no-pager -n 5 2>&1"))

# VRAM
print("\n=== VRAM with MuseTalk ===")
print(run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader"))

# Restart Gateway
print("\n=== Restart Gateway ===")
run("echo pepe1234 | sudo -S systemctl restart ai-hub-gateway 2>&1")
time.sleep(8)

# Final status
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
            mark = "OK" if sv.get("status") == "online" else "--"
            print(f"    [{mark}] {sv.get('name','?'):30s} {sv.get('status','?'):10s} :{sv.get('port','?')}")
    except Exception as ex:
        print(f"  Error: {ex}")

s.close()
print("\nDone!")
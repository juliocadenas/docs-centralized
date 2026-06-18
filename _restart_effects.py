"""Restart effects + wait for MuseTalk + final verify."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=60):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:400] if err else "")

# Restart effects (rembg+upscale - lightweight)
print("=== Restart Effects ===")
run("echo pepe1234 | sudo -S systemctl start effects 2>&1")
time.sleep(10)

# Wait for MuseTalk to finish loading
print("=== Wait for MuseTalk (40s) ===")
time.sleep(40)
mt = run("systemctl is-active musetalk 2>&1")
print(f"  MuseTalk systemd: {mt}")
code = run("curl -s -o /dev/null -w " + chr(39) + "%{http_code}" + chr(39) + " --max-time 30 http://localhost:8041/ 2>&1")
print(f"  MuseTalk port 8041: {code}")
if code != "200":
    print(run("journalctl -u musetalk --no-pager -n 8 2>&1"))

# Restart Gateway to refresh
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

print(f"\n=== VRAM ===")
print(run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader"))

s.close()
print("\nDone!")
"""Wait for services to load, then check final status."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=60):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:400] if err else "")

# Check systemd states
print("=== Systemd states ===")
for svc in ["musetalk", "latentsync", "liveportrait", "hallo2", "effects"]:
    st = run("systemctl is-active " + svc + " 2>&1")
    print(f"  {svc}: {st}")

# Check ports with generous timeout
print("\n=== Port checks (30s timeout each) ===")
for port, name in [(8041, "MuseTalk"), (8043, "LatentSync"), (8044, "LivePortrait"), (8070, "Hallo2"), (8050, "Rembg"), (8051, "Upscale")]:
    code = run("curl -s -o /dev/null -w " + chr(39) + "%{http_code}" + chr(39) + " --max-time 30 http://localhost:" + str(port) + "/ 2>&1")
    print(f"  :{port} {name}: {code}")

# Check MuseTalk logs specifically
print("\n=== MuseTalk last logs ===")
print(run("journalctl -u musetalk --no-pager -n 10 2>&1"))

# Check if rembg still works (numpy conflict)
print("\n=== Rembg check (numpy conflict?) ===")
print(run("curl -s -o /dev/null -w " + chr(39) + "%{http_code}" + chr(39) + " http://localhost:8050/ 2>&1"))

# Final Gateway status
print("\n=== Gateway status ===")
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
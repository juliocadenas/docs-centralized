"""Wait for server to come back after reboot, then verify."""
import paramiko, time, socket

SERVER = "100.105.27.27"
PORT_SSH = 22

def wait_for_ssh(timeout=300):
    """Wait until SSH is reachable."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((SERVER, PORT_SSH))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(5)
    return False

print("=== Waiting for server reboot (up to 5 min) ===")
print("  (reboot was scheduled +1 min, then boot takes ~30s)")
time.sleep(70)  # Wait for the 1-minute shutdown timer

if wait_for_ssh():
    print("  SSH reachable!")
    
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(SERVER, username="pepe", password="pepe1234", timeout=15)
    
    def run(cmd, t=30):
        try:
            _, o, e = s.exec_command(cmd, timeout=t)
            return o.read().decode().strip()
        except:
            return "(timeout)"
    
    # Check uptime (confirm reboot happened)
    uptime = run("uptime")
    print(f"\n=== UPTIME ===\n  {uptime}")
    
    # Check GPU
    print("\n=== GPU STATUS ===")
    print(run("nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader 2>&1"))
    
    # Check what auto-started
    print("\n=== AUTO-STARTED SERVICES ===")
    for svc in ["ollama", "ai-hub-gateway", "piper_tts", "whisper_stt"]:
        print(f"  {svc}: {run('systemctl is-active ' + svc + ' 2>&1')}")
    
    # Check heavy services are STOPPED
    print("\n=== HEAVY SERVICES (should be stopped) ===")
    for svc in ["comfyui", "documusic", "wan2gp", "musetalk", "latentsync", "liveportrait", "hallo2", "effects"]:
        print(f"  {svc}: {run('systemctl is-active ' + svc + ' 2>&1')}")
    
    # Gateway status
    print("\n=== GATEWAY STATUS ===")
    status_raw = run("curl -s --max-time 10 http://localhost:9000/v1/status")
    if status_raw:
        import json
        try:
            d = json.loads(status_raw)
            online = sum(1 for sv in d.get("services", []) if sv.get("status") == "online")
            total = len(d.get("services", []))
            print(f"  Online: {online}/{total}")
            for sv in d.get("services", []):
                mark = "OK" if sv.get("status") == "online" else "--"
                print(f"    [{mark}] {sv.get('name','?'):30s} {sv.get('status','?'):10s}")
        except Exception as ex:
            print(f"  Error: {ex}")
    else:
        print("  Gateway not responding yet")
    
    s.close()
else:
    print("  SSH not reachable after 5 min!")

print("\nDone!")
"""GPU recovery + stable config. The GPU driver crashed from VRAM exhaustion."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=120):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:400] if err else "")

# Step 1: Stop ALL GPU services immediately
print("=== STOP ALL GPU SERVICES ===")
gpu_svcs = ["comfyui", "documusic", "wan2gp", "musetalk", "latentsync", "liveportrait", "hallo2", "effects", "upscale"]
for svc in gpu_svcs:
    run("echo pepe1234 | sudo -S systemctl stop " + svc + " 2>&1")
    print(f"  Stopped: {svc}")
time.sleep(5)

# Step 2: Kill any remaining python GPU processes
print("\n=== KILL GPU PROCESSES ===")
print(run("echo pepe1234 | sudo -S fuser -k /dev/nvidia* 2>&1"))
time.sleep(3)
print(run("ps aux | grep -E 'python|comfy|gradio' | grep -v grep | awk '{print $2}' | head -5"))

# Step 3: Try to reload nvidia driver modules
print("\n=== RELOAD NVIDIA MODULES ===")
# First check if nvidia-smi works
check = run("nvidia-smi --query-gpu=memory.used --format=csv,noheader 2>&1")
print(f"  Before: {check}")

if "No devices" in check or "Unknown" in check or "ERR" in check:
    print("  GPU driver crashed! Attempting module reload...")
    run("echo pepe1234 | sudo -S rmmod nvidia_uvm 2>&1")
    run("echo pepe1234 | sudo -S rmmod nvidia_drm 2>&1")
    run("echo pepe1234 | sudo -S rmmod nvidia_modeset 2>&1")
    run("echo pepe1234 | sudo -S rmmod nvidia 2>&1")
    time.sleep(2)
    run("echo pepe1234 | sudo -S modprobe nvidia 2>&1")
    time.sleep(3)
    run("echo pepe1234 | sudo -S modprobe nvidia_uvm 2>&1")
    run("echo pepe1234 | sudo -S modprobe nvidia_drm 2>&1")
    run("echo pepe1234 | sudo -S modprobe nvidia_modeset 2>&1")
    time.sleep(5)
    check2 = run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader 2>&1")
    print(f"  After reload: {check2}")
else:
    print("  GPU OK")

# Step 4: Disable ALL heavy services from auto-start at boot
# Only essentials should auto-start
print("\n=== DISABLE AUTO-START FOR HEAVY SERVICES ===")
heavy = ["comfyui", "documusic", "wan2gp", "musetalk", "latentsync", "liveportrait", "hallo2", "effects", "upscale"]
for svc in heavy:
    r = run("echo pepe1234 | sudo -S systemctl disable " + svc + " 2>&1")
    print(f"  {svc}: disabled")

# Step 5: Only start essentials + lightweight services
print("\n=== START ESSENTIALS ONLY ===")
# Ollama (always on)
print(f"  Ollama: {run('systemctl is-active ollama 2>&1')}")
# Effects (rembg+upscale - very lightweight, CPU-ish)
run("echo pepe1234 | sudo -S systemctl start effects 2>&1")
time.sleep(8)
print(f"  Effects: {run('systemctl is-active effects 2>&1')}")

# Step 6: Start Gateway
print("\n=== RESTART GATEWAY ===")
run("echo pepe1234 | sudo -S systemctl restart ai-hub-gateway 2>&1")
time.sleep(8)
print(f"  Gateway: {run('systemctl is-active ai-hub-gateway 2>&1')}")

# Final check
print("\n=== FINAL STATUS ===")
print(f"  GPU: {run('nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader 2>&1')}")
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
            print(f"    [{mark}] {sv.get('name','?'):30s} {sv.get('status','?'):10s}")
    except:
        print(f"  RAW: {status_raw[:200]}")

s.close()
print("\nDone! Heavy services are on-demand only (managed by Gateway).")
"""Force kill GPU processes and reboot server cleanly."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=30):
    try:
        _, o, e = s.exec_command(cmd, timeout=t)
        return o.read().decode().strip()
    except:
        return "(timeout/ssh closed)"

# Step 1: Force kill ALL processes using GPU devices
print("=== FORCE KILL GPU PROCESSES ===")
# Kill by PID from fuser output
pids = run("echo pepe1234 | sudo -S fuser /dev/nvidia* 2>/dev/null")
print(f"  GPU PIDs: {pids}")
if pids:
    for pid in pids.split():
        pid = pid.strip().rstrip('m').rstrip('e')
        if pid.isdigit():
            run(f"echo pepe1234 | sudo -S kill -9 {pid} 2>&1")
            print(f"  Killed PID {pid}")
time.sleep(3)

# Step 2: Kill any remaining python processes related to AI
print("\n=== KILL AI PYTHON PROCESSES ===")
python_pids = run("ps aux | grep -E 'python.*comfy|python.*gradio|python.*musetalk|python.*wan|python.*documusic|python.*hallo|python.*latent|python.*liveportrait' | grep -v grep | awk '{print $2}'")
if python_pids:
    for pid in python_pids.strip().split('\n'):
        pid = pid.strip()
        if pid.isdigit():
            run(f"echo pepe1234 | sudo -S kill -9 {pid} 2>&1")
            print(f"  Killed python PID {pid}")
time.sleep(2)

# Step 3: Stop Ollama (it holds GPU)
print("\n=== STOP OLLAMA ===")
run("echo pepe1234 | sudo -S systemctl stop ollama 2>&1")
print("  Ollama stopped")
time.sleep(3)

# Step 4: Check if nvidia-smi recovered
print("\n=== CHECK GPU ===")
check = run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader 2>&1")
print(f"  GPU status: {check}")

if "No devices" in check or "Unknown" in check or "Unable" in check:
    print("\n=== GPU STILL CRASHED - NEED REBOOT ===")
    print("  Scheduling reboot in 5 seconds...")
    # Use shutdown -r with a short delay
    run("echo pepe1234 | sudo -S shutdown -r +1 'GPU driver crashed - scheduled reboot by AI Hub recovery' 2>&1")
    print("  Reboot scheduled in 1 minute!")
    print("  The server will come back with only Ollama + Gateway auto-starting.")
    print("  Heavy services (comfyui, musetalk, etc.) will be on-demand via Gateway API.")
else:
    print("\n=== GPU RECOVERED ===")
    # Restart essentials
    run("echo pepe1234 | sudo -S systemctl start ollama 2>&1")
    time.sleep(5)
    run("echo pepe1234 | sudo -S systemctl start effects 2>&1")
    time.sleep(5)
    run("echo pepe1234 | sudo -S systemctl restart ai-hub-gateway 2>&1")
    print("  Essentials restarted!")

s.close()
print("\nDone!")
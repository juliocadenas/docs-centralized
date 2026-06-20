#!/usr/bin/env python3
"""GPU PCI reset v2 - proper sudo redirect handling."""
import paramiko, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run(client, cmd, timeout=30):
    print(f"\n>>> {cmd}", flush=True)
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        stdout.channel.settimeout(timeout)
        out = stdout.read().decode(errors='replace')
        err = stderr.read().decode(errors='replace')
        if out.strip():
            print(out.rstrip(), flush=True)
        if err.strip() and 'password' not in err.lower() and 'contraseña' not in err.lower():
            print(f"[stderr] {err.rstrip()}", flush=True)
        return out, err
    except Exception as e:
        print(f"[error] {e}", flush=True)
        return '', str(e)

def sudo_run(client, cmd, timeout=30):
    """Run with sudo - proper redirect handling via bash -c."""
    full_cmd = f"echo '{PASS}' | sudo -S bash -c \"{cmd}\""
    return run(client, full_cmd, timeout=timeout)

def main():
    print("=== Connecting to NAB9 ===", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("Connected!", flush=True)
    
    print("\n" + "="*60, flush=True)
    print("GPU PCI RESET v2 (proper sudo)", flush=True)
    print("="*60, flush=True)
    
    # Step 1: Stop GPU containers first to free the modules
    print("\n--- 1. STOP GPU CONTAINERS ---", flush=True)
    run(client, "docker stop ollama_hub 2>/dev/null; echo 'ollama stopped'", timeout=30)
    run(client, "docker stop documusic_backend 2>/dev/null; echo 'documusic stopped'", timeout=30)
    time.sleep(5)
    
    # Step 2: Check what's using nvidia
    print("\n--- 2. PROCESSES USING NVIDIA ---", flush=True)
    sudo_run(client, "lsof /dev/nvidia* 2>/dev/null | head -10 || echo 'no lsof'")
    run(client, "fuser /dev/nvidia* 2>/dev/null || echo 'no fuser'")
    
    # Step 3: Kill any process using GPU
    print("\n--- 3. FORCE KILL GPU PROCESSES ---", flush=True)
    sudo_run(client, "fuser -k /dev/nvidia* 2>/dev/null; echo 'killed'")
    time.sleep(3)
    
    # Step 4: Try to unload modules
    print("\n--- 4. UNLOAD NVIDIA MODULES ---", flush=True)
    sudo_run(client, "modprobe -r nvidia_uvm 2>&1 || echo 'uvm in use'")
    sudo_run(client, "modprobe -r nvidia_modeset nvidia_drm 2>&1 || echo 'drm in use'")
    sudo_run(client, "modprobe -r nvidia 2>&1 || echo 'nvidia in use'")
    time.sleep(2)
    
    # Step 5: PCI FLR (Function Level Reset)
    print("\n--- 5. PCI FUNCTION LEVEL RESET ---", flush=True)
    # Method 1: PCI remove + rescan
    sudo_run(client, "echo 1 > /sys/bus/pci/devices/0000:01:00.0/remove")
    time.sleep(5)
    sudo_run(client, "echo 1 > /sys/bus/pci/rescan")
    time.sleep(10)
    
    # Check if GPU is back
    print("\n--- 6. CHECK GPU ---", flush=True)
    run(client, "lspci | grep -i nvidia")
    
    # Reload modules
    print("\n--- 7. RELOAD NVIDIA MODULES ---", flush=True)
    sudo_run(client, "modprobe nvidia 2>&1")
    time.sleep(5)
    sudo_run(client, "modprobe nvidia_uvm nvidia_modeset nvidia_drm 2>&1")
    time.sleep(3)
    
    # Step 8: Try nvidia-smi
    print("\n--- 8. NVIDIA-SMI CHECK ---", flush=True)
    out, _ = run(client, "nvidia-smi 2>&1 | head -15")
    
    if 'RTX 5080' in out or '16GB' in out or 'MiB' in out:
        print("\n[OK] GPU RECOVERED SUCCESSFULLY!", flush=True)
        
        # Restart containers
        print("\n--- 9. RESTART CONTAINERS ---", flush=True)
        run(client, "docker start ollama_hub 2>&1", timeout=30)
        run(client, "docker start documusic_backend 2>&1", timeout=30)
        
        print("\n--- 10. FINAL DOCKER STATUS ---", flush=True)
        run(client, "docker ps --format 'table {{.Names}}\\t{{.Status}}'")
    else:
        print("\n[FAIL] GPU still not responding after PCI reset", flush=True)
        print("\n[ACTION REQUIRED] HARD POWER CYCLE NEEDED:", flush=True)
        print("  1. SSH: sudo systemctl poweroff", flush=True)
        print("  2. Wait 30 seconds physically", flush=True)
        print("  3. Press power button to turn on", flush=True)
        print("  OR: Use IPMI/Wake-on-LAN if available", flush=True)
    
    client.close()

if __name__ == "__main__":
    main()
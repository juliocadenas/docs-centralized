#!/usr/bin/env python3
"""Try to recover GPU without full reboot - PCI reset + module reload."""
import paramiko, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run(client, cmd, timeout=30, sudo=True):
    if sudo:
        cmd = f"echo '{PASS}' | sudo -S {cmd}"
    print(f"\n>>> {cmd}", flush=True)
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        stdout.channel.settimeout(timeout)
        out = stdout.read().decode(errors='replace')
        err = stderr.read().decode(errors='replace')
        if out.strip():
            print(out.rstrip(), flush=True)
        if err.strip() and 'password' not in err.lower():
            print(f"[stderr] {err.rstrip()}", flush=True)
        return out, err
    except Exception as e:
        print(f"[error] {e}", flush=True)
        return '', str(e)

def main():
    print("=== Connecting to NAB9 ===", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("Connected!", flush=True)
    
    print("\n" + "="*60, flush=True)
    print("GPU RECOVERY ATTEMPT (no reboot)", flush=True)
    print("="*60, flush=True)
    
    # Step 1: Current nvidia-smi status
    print("\n--- 1. CURRENT GPU STATUS ---", flush=True)
    run(client, "nvidia-smi 2>&1 | head -5", sudo=False)
    
    # Step 2: Try PCI bus reset (this is the most likely to work)
    print("\n--- 2. PCI BUS RESET ---", flush=True)
    # Remove from PCI bus then rescan
    run(client, "echo 1 > /sys/bus/pci/devices/0000:01:00.0/remove", sudo=True)
    time.sleep(3)
    run(client, "echo 1 > /sys/bus/pci/rescan", sudo=True)
    time.sleep(5)
    
    # Check if GPU came back
    print("\n--- 3. CHECK GPU AFTER RESET ---", flush=True)
    run(client, "lspci | grep -i nvidia", sudo=False)
    run(client, "nvidia-smi 2>&1 | head -10", sudo=False)
    
    # If still not working, try module reload
    print("\n--- 4. MODULE RELOAD ATTEMPT ---", flush=True)
    run(client, "modprobe -r nvidia_uvm nvidia_drm nvidia_modeset nvidia 2>&1 || echo 'Cannot unload (in use)'", sudo=True)
    time.sleep(2)
    run(client, "modprobe nvidia 2>&1 && echo 'nvidia loaded' || echo 'failed'", sudo=True)
    time.sleep(3)
    run(client, "nvidia-smi 2>&1 | head -10", sudo=False)
    
    # Final status
    print("\n" + "="*60, flush=True)
    print("FINAL STATUS", flush=True)
    print("="*60, flush=True)
    rc_out, _ = run(client, "nvidia-smi --query-gpu=name,memory.total,memory.used,temperature.gpu --format=csv 2>&1", sudo=False)
    
    if 'RTX' in rc_out or 'GB' in rc_out:
        print("\n[OK] GPU RECOVERED!", flush=True)
        
        # Start essential GPU containers
        print("\n--- Starting GPU containers ---", flush=True)
        run(client, "docker ps -a --filter name=comfy --format '{{.Names}}'", sudo=False)
        run(client, "docker ps -a --format '{{.Names}}' | head -10", sudo=False)
    else:
        print("\n[FAIL] GPU still not responding", flush=True)
        print("HARD RESET REQUIRED: Power off the server completely, wait 30s, power on", flush=True)
        print("This means physically pressing the power button", flush=True)
    
    client.close()

if __name__ == "__main__":
    main()
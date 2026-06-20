#!/usr/bin/env python3
"""Deep GPU diagnostics with retry - check kernel modules, dmesg, lspci."""
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
        if err.strip():
            print(f"[stderr] {err.rstrip()}", flush=True)
        return out, err
    except Exception as e:
        print(f"[error] {e}", flush=True)
        return '', str(e)

def main():
    print("=== Waiting for NAB9 ===", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for i in range(30):
        try:
            print(f"  Attempt {i+1}/30...", flush=True)
            client.connect(HOST, username=USER, password=PASS, timeout=10)
            print("  Connected!", flush=True)
            break
        except Exception as e:
            print(f"  Not yet ({type(e).__name__})", flush=True)
            time.sleep(15)
    else:
        print("ERROR: Server not reachable after 30 retries", flush=True)
        sys.exit(1)
    
    print("\n" + "="*60, flush=True)
    print("DEEP GPU DIAGNOSTICS", flush=True)
    print("="*60, flush=True)
    
    print("\n--- 1. PCI DEVICE ---", flush=True)
    run(client, "lspci | grep -i -E 'vga|nvidia|3d|display'")
    
    print("\n--- 2. KERNEL MODULES ---", flush=True)
    run(client, "lsmod | grep -i -E 'nvidia|nouveau'")
    
    print("\n--- 3. DMESG GPU ---", flush=True)
    run(client, "dmesg | grep -i -E 'nvidia|nouveau|gpu|nvrm' | tail -30")
    
    print("\n--- 4. NVIDIA DEVICES ---", flush=True)
    run(client, "ls -la /dev/nvidia* 2>/dev/null || echo 'No /dev/nvidia devices'")
    run(client, "nvidia-smi --version 2>/dev/null | head -5 || echo 'nvidia-smi not found'")
    
    print("\n--- 5. NVIDIA PACKAGES ---", flush=True)
    run(client, "dpkg -l 2>/dev/null | grep -i nvidia | head -10 || echo 'no dpkg'")
    
    print("\n--- 6. NVIDIA MODULE FILES ---", flush=True)
    run(client, "modinfo nvidia 2>/dev/null | head -5 || echo 'no nvidia module'")
    run(client, "find /lib/modules/$(uname -r) -name 'nvidia*' 2>/dev/null | head -5")
    
    print("\n--- 7. SYSTEM INFO ---", flush=True)
    run(client, "uptime && uname -r && cat /etc/os-release | head -2")
    
    print("\n--- 8. DOCKER STATUS ---", flush=True)
    run(client, "docker ps --format 'table {{.Names}}\t{{.Status}}'")
    
    print("\n--- 9. GATEWAY ---", flush=True)
    run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/v1/status 2>/dev/null || echo 'down'")
    
    client.close()
    print("\n=== Done ===", flush=True)

if __name__ == "__main__":
    main()
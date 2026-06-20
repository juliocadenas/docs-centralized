#!/usr/bin/env python3
"""Restore containers we stopped + check Wake-on-LAN + prepare for power cycle."""
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
    full_cmd = f"echo '{PASS}' | sudo -S bash -c \"{cmd}\""
    return run(client, full_cmd, timeout=timeout)

def main():
    print("=== Connecting to NAB9 ===", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("Connected!", flush=True)
    
    print("\n" + "="*60, flush=True)
    print("RESTORING SERVICES + POWER CYCLE PREP", flush=True)
    print("="*60, flush=True)
    
    # 1. Restart containers we stopped
    print("\n--- 1. RESTARTING CONTAINERS ---", flush=True)
    run(client, "docker start ollama_hub 2>&1", timeout=30)
    run(client, "docker start documusic_backend 2>&1", timeout=30)
    time.sleep(3)
    
    # 2. Check Docker status
    print("\n--- 2. DOCKER STATUS ---", flush=True)
    run(client, "docker ps --format 'table {{.Names}}\\t{{.Status}}'")
    
    # 3. Check if Wake-on-LAN is available (for remote power on)
    print("\n--- 3. WAKE-ON-LAN CHECK ---", flush=True)
    run(client, "ip link show | grep -A1 'eno\\|enp' | head -5")
    sudo_run(client, "ethtool $(ip route get 192.168.1.1 | grep -oP 'dev \\K\\S+') 2>/dev/null | grep -i wake")
    
    # 4. Get MAC address for WoL
    print("\n--- 4. MAC ADDRESS FOR WOL ---", flush=True)
    run(client, "ip link show | grep -A1 'state UP' | grep link/ether | head -1")
    
    # 5. Enable WoL if possible
    print("\n--- 5. ENABLE WAKE-ON-LAN ---", flush=True)
    iface = run(client, "ip route get 192.168.1.1 2>/dev/null | grep -oP 'dev \\K\\S+'")[0].strip()
    if iface:
        sudo_run(client, f"ethtool -s {iface} wol g 2>&1 || echo 'WoL not supported'")
    
    # 6. Gateway check
    print("\n--- 6. GATEWAY STATUS ---", flush=True)
    run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/v1/status 2>/dev/null")
    
    # 7. Prepare auto-start script for post power cycle
    print("\n--- 7. POST-BOOT AUTO RECOVERY SCRIPT ---", flush=True)
    recovery_script = """#!/bin/bash
# Auto-recovery after power cycle
# This will be placed in /mnt/seagate/scripts/post_powercycle.sh

echo "=== Post Power-Cycle Recovery ==="
sleep 10

# Wait for Docker to be ready
while ! docker info >/dev/null 2>&1; do
    echo "Waiting for Docker..."
    sleep 5
done

# Start all containers
echo "Starting containers..."
docker start ollama_hub 2>/dev/null
docker start documusic_backend 2>/dev/null
docker start ai-hub-studio 2>/dev/null
docker start backend-redis-1 2>/dev/null

# Verify GPU
echo "Checking GPU..."
nvidia-smi

# Pull and start XTTS-v2
echo "Starting XTTS-v2..."
mkdir -p /mnt/seagate/models/voice/tts/xtts-v2
docker pull ghcr.io/coqui-ai/xtts-streaming-server:latest 2>/dev/null
docker rm -f xtts-v2 2>/dev/null
docker run -d --name xtts-v2 --gpus all -p 8011:80 \\
    -v /mnt/seagate/models/voice/tts/xtts-v2:/root/.local/share/coqui \\
    -e COQUI_TOS_AGREED=1 --restart unless-stopped \\
    ghcr.io/coqui-ai/xtts-streaming-server:latest

echo "=== Recovery Complete ==="
docker ps --format 'table {{.Names}}\\t{{.Status}}'
"""
    sudo_run(client, f"cat > /tmp/post_powercycle.sh << 'SCRIPT_EOF'\n{recovery_script}\nSCRIPT_EOF")
    sudo_run(client, "chmod +x /tmp/post_powercycle.sh")
    print("Recovery script saved to /tmp/post_powercycle.sh on server", flush=True)
    
    client.close()
    print("\n=== Done ===", flush=True)

if __name__ == "__main__":
    main()
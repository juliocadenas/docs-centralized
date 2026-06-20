#!/usr/bin/env python3
"""Post-reboot recovery: verify GPU, restart services, deploy XTTS-v2."""
import paramiko, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run(client, cmd, timeout=30):
    """Run command with proper timeout handling."""
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
        return stdout.channel.recv_exit_status(), out, err
    except Exception as e:
        print(f"[error] {e}", flush=True)
        return -1, '', str(e)

def connect_with_retry(host, user, pwd, max_retries=20):
    """Wait for server to come back online after reboot."""
    print("=== Waiting for NAB9 to come back online ===", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for i in range(max_retries):
        try:
            print(f"  Attempt {i+1}/{max_retries}...", flush=True)
            client.connect(host, username=user, password=pwd, timeout=10)
            print("  ✅ Connected!", flush=True)
            return client
        except Exception as e:
            print(f"  ❌ Not yet ({e})", flush=True)
            time.sleep(15)
    
    print("ERROR: Server not reachable after retries", flush=True)
    sys.exit(1)

def main():
    client = connect_with_retry(HOST, USER, PASS)
    
    # 1. Verify GPU
    print("\n" + "="*50, flush=True)
    print("1. GPU VERIFICATION", flush=True)
    print("="*50, flush=True)
    rc, gpu_out, _ = run(client, "nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader")
    
    if rc != 0 or "No devices" in gpu_out:
        print("\n❌ CRITICAL: GPU still not detected!", flush=True)
        print("Manual intervention needed.", flush=True)
        client.close()
        sys.exit(1)
    
    print(f"\n✅ GPU detected: {gpu_out.strip()}", flush=True)
    
    # 2. Check Docker and restart essential containers
    print("\n" + "="*50, flush=True)
    print("2. DOCKER CONTAINERS STATUS", flush=True)
    print("="*50, flush=True)
    run(client, "docker ps --format 'table {{.Names}}\t{{.Status}}'")
    
    # 3. Start XTTS-v2 pull in BACKGROUND (nohup) to avoid timeout
    print("\n" + "="*50, flush=True)
    print("3. STARTING XTTS-v2 PULL IN BACKGROUND", flush=True)
    print("="*50, flush=True)
    run(client, "mkdir -p /mnt/seagate/models/voice/tts/xtts-v2")
    
    # Use nohup to run pull in background, log to file
    run(client, 
        "nohup bash -c 'docker pull ghcr.io/coqui-ai/xtts-streaming-server:latest > /tmp/xtts_pull.log 2>&1 && "
        "docker rm -f xtts-v2 2>/dev/null; "
        "docker run -d --name xtts-v2 --gpus all -p 8011:80 "
        "-v /mnt/seagate/models/voice/tts/xtts-v2:/root/.local/share/coqui "
        "-e COQUI_TOS_AGREED=1 --restart unless-stopped "
        "ghcr.io/coqui-ai/xtts-streaming-server:latest >> /tmp/xtts_pull.log 2>&1' &",
        timeout=5  # Just fire and forget
    )
    print("✅ XTTS-v2 pull started in background (/tmp/xtts_pull.log)", flush=True)
    print("   Check status: ssh pepe@100.105.27.27 'cat /tmp/xtts_pull.log'", flush=True)
    
    # 4. Start ComfyUI container
    print("\n" + "="*50, flush=True)
    print("4. STARTING COMFYUI", flush=True)
    print("="*50, flush=True)
    
    # Check if there's a compose file or standalone container
    rc, out, _ = run(client, "ls /mnt/seagate/comfyui/docker-compose.yml 2>/dev/null || ls /mnt/seagate/ai-hub-gateway/docker-compose.yml 2>/dev/null || echo 'no-compose'")
    
    if 'no-compose' not in out:
        compose_file = out.strip().split('\n')[0]
        print(f"\nFound compose file: {compose_file}", flush=True)
        # Don't start all services, just comfyui
        run(client, f"cd $(dirname {compose_file}) && docker compose up -d comfyui 2>&1 || true", timeout=120)
    else:
        # Check for existing comfyui standalone
        rc, out2, _ = run(client, "docker ps -a --filter name=comfy --format '{{.Names}}'")
        if 'comfy' not in out2.lower():
            print("ComfyUI container doesn't exist. Checking for startup scripts...", flush=True)
            run(client, "ls /mnt/seagate/comfyui/ 2>/dev/null | head -10 || echo 'no comfyui dir'")
            run(client, "find /mnt/seagate -name 'run_comfyui*' -o -name 'start_comfyui*' 2>/dev/null | head -5")
        else:
            run(client, "docker start $(docker ps -a --filter name=comfy --format '{{.Names}}' | head -1)")
    
    # 5. Verify Gateway
    print("\n" + "="*50, flush=True)
    print("5. GATEWAY STATUS", flush=True)
    print("="*50, flush=True)
    run(client, "systemctl is-active ai-hub-gateway.service 2>/dev/null || echo 'not-systemd'")
    run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/v1/status || echo 'gateway-down'")
    
    # 6. Final Docker status
    print("\n" + "="*50, flush=True)
    print("6. FINAL STATUS", flush=True)
    print("="*50, flush=True)
    run(client, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    
    client.close()
    print("\n✅ Recovery script complete!", flush=True)
    print("NOTE: XTTS-v2 is being pulled in background. Check in 5-10 min:", flush=True)
    print("  ssh pepe@100.105.27.27 'cat /tmp/xtts_pull.log; docker ps | grep xtts'", flush=True)

if __name__ == "__main__":
    main()
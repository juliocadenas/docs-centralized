#!/usr/bin/env python3
"""Wait for server + full recovery + XTTS-v2 deploy."""
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

def wait_for_server():
    """Wait up to 15 min for server."""
    print("=== Waiting for NAB9 to come back online (up to 15 min) ===", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for i in range(60):
        try:
            print(f"  Attempt {i+1}/60...", flush=True)
            client.connect(HOST, username=USER, password=PASS, timeout=10)
            print("  CONNECTED!", flush=True)
            return client
        except Exception as e:
            print(f"  Not yet ({type(e).__name__})", flush=True)
            time.sleep(15)
    
    print("ERROR: Server not reachable after 15 min", flush=True)
    sys.exit(1)

def main():
    client = wait_for_server()
    
    print("\n" + "="*60, flush=True)
    print("FULL SYSTEM RECOVERY", flush=True)
    print("="*60, flush=True)
    
    # 1. Verify GPU FIRST - critical
    print("\n--- 1. GPU VERIFICATION ---", flush=True)
    gpu_out, _ = run(client, "nvidia-smi 2>&1 | head -15")
    
    if "No devices" in gpu_out or "Unknown Error" in gpu_out:
        print("\n*** GPU STILL DOWN ***", flush=True)
        print("The hard power cycle did NOT fix the GPU.", flush=True)
        print("This indicates a HARDWARE problem.", flush=True)
        print("Check:", flush=True)
        print("  - GPU power cables (6+2 pin PCIe)", flush=True)
        print("  - GPU seated properly in PCIe slot", flush=True)
        print("  - Reseat the GPU physically", flush=True)
    else:
        print(f"\n*** GPU IS BACK! ***\n{gpu_out}", flush=True)
    
    # 2. Start containers
    print("\n--- 2. STARTING CONTAINERS ---", flush=True)
    run(client, "docker start ollama_hub 2>&1", timeout=30)
    run(client, "docker start documusic_backend 2>&1", timeout=30)
    run(client, "docker start ai-hub-studio 2>&1", timeout=30)
    run(client, "docker start backend-redis-1 2>&1", timeout=30)
    
    # 3. Docker status
    print("\n--- 3. DOCKER STATUS ---", flush=True)
    run(client, "docker ps --format 'table {{.Names}}\\t{{.Status}}'")
    
    # 4. Gateway check
    print("\n--- 4. GATEWAY ---", flush=True)
    run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/v1/status")
    
    # 5. Deploy XTTS-v2 IF GPU is working
    if "No devices" not in gpu_out and "Unknown Error" not in gpu_out:
        print("\n--- 5. DEPLOY XTTS-v2 ---", flush=True)
        run(client, "mkdir -p /mnt/seagate/models/voice/tts/xtts-v2")
        
        # Run pull + container in background to avoid timeout
        xtts_cmd = (
            "nohup bash -c '"
            "docker pull ghcr.io/coqui-ai/xtts-streaming-server:latest > /tmp/xtts_pull.log 2>&1 && "
            "docker rm -f xtts-v2 2>/dev/null; "
            "docker run -d --name xtts-v2 --gpus all -p 8011:80 "
            "-v /mnt/seagate/models/voice/tts/xtts-v2:/root/.local/share/coqui "
            "-e COQUI_TOS_AGREED=1 --restart unless-stopped "
            "ghcr.io/coqui-ai/xtts-streaming-server:latest >> /tmp/xtts_pull.log 2>&1"
            "' &"
        )
        run(client, xtts_cmd, timeout=5)
        print("XTTS-v2 deploy started in background", flush=True)
    
    # 6. Final status
    print("\n" + "="*60, flush=True)
    print("RECOVERY SUMMARY", flush=True)
    print("="*60, flush=True)
    run(client, "nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader 2>&1")
    run(client, "docker ps --format 'table {{.Names}}\\t{{.Status}}'")
    
    client.close()
    print("\n=== DONE ===", flush=True)

if __name__ == "__main__":
    main()
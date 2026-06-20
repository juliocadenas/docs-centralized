#!/usr/bin/env python3
"""Diagnose ComfyUI and deploy XTTS-v2 via paramiko SSH."""
import paramiko, sys, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run(client, cmd, timeout=60):
    print(f"\n>>> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    if out.strip():
        print(out.rstrip())
    if err.strip():
        print(f"[stderr] {err.rstrip()}")
    return stdout.channel.recv_exit_status(), out, err

def main():
    print("=== Connecting to NAB9 ===")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("Connected!")

    # 1. Check ComfyUI status
    print("\n" + "="*50)
    print("1. COMFYUI DIAGNOSIS")
    print("="*50)
    run(client, "docker ps -a --filter name=comfy --format '{{.Names}}:{{.Status}}:{{.Ports}}'")
    run(client, "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://localhost:8188/ || echo 'no-response'")

    # 2. Check if ComfyUI container exists and restart if needed
    rc, out, _ = run(client, "docker ps -a --filter name=comfy --format '{{.Names}}'")
    comfy_exists = 'comfy' in out.lower()
    if comfy_exists:
        print("\n--- ComfyUI logs (last 15 lines) ---")
        run(client, "docker logs --tail 15 $(docker ps -a --filter name=comfy --format '{{.Names}}' | head -1) 2>&1")

    # 3. GPU status
    print("\n" + "="*50)
    print("2. GPU STATUS")
    print("="*50)
    run(client, "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader")

    # 4. Deploy XTTS-v2
    print("\n" + "="*50)
    print("3. DEPLOY XTTS-v2")
    print("="*50)

    # Create dirs
    run(client, "mkdir -p /mnt/seagate/models/voice/tts/xtts-v2 /mnt/seagate/links/tts")

    # Check if xtts container already exists
    rc, out, _ = run(client, "docker ps -a --filter name=xtts-v2 --format '{{.Names}}'")
    if 'xtts-v2' in out:
        print("XTTS-v2 container exists, removing...")
        run(client, "docker rm -f xtts-v2 2>/dev/null")

    # Pull image
    print("\n--- Pulling XTTS-v2 image (may take a while) ---")
    rc, _, _ = run(client, "docker pull ghcr.io/coqui-ai/xtts-streaming-server:latest 2>&1 | tail -5", timeout=300)
    if rc != 0:
        print("WARNING: Pull may have failed, trying to start anyway...")

    # Start container
    print("\n--- Starting XTTS-v2 container ---")
    cmd = """docker run -d \
      --name xtts-v2 \
      --gpus all \
      -p 8011:80 \
      -v /mnt/seagate/models/voice/tts/xtts-v2:/root/.local/share/coqui \
      -e COQUI_TOS_AGREED=1 \
      --restart unless-stopped \
      ghcr.io/coqui-ai/xtts-streaming-server:latest"""
    rc, _, _ = run(client, cmd)
    if rc == 0:
        print("✅ XTTS-v2 container started on port 8011")
    else:
        print("❌ Failed to start XTTS-v2")

    # 5. Summary
    print("\n" + "="*50)
    print("4. FINAL STATUS")
    print("="*50)
    run(client, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")

    client.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
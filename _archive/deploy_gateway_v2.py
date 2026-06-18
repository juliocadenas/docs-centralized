"""
Deploy AI Hub Gateway v2.0 to the server.
Uploads all updated files and restarts the service.
"""
import subprocess
import sys
import os
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SERVER = "julio@100.105.27.27"
REMOTE_BASE = "/mnt/seagate/ai-hub-gateway-v2"

FILES_TO_UPLOAD = [
    "ai-hub-gateway/main.py",
    "ai-hub-gateway/requirements.txt",
    "ai-hub-gateway/Dockerfile",
    "ai-hub-gateway/docker-compose.yml",
    "ai-hub-gateway/gateway/__init__.py",
    "ai-hub-gateway/gateway/config.py",
    "ai-hub-gateway/gateway/gpu_manager.py",
    "ai-hub-gateway/gateway/models/__init__.py",
    "ai-hub-gateway/gateway/models/schemas.py",
    "ai-hub-gateway/gateway/routers/__init__.py",
    "ai-hub-gateway/gateway/routers/llm.py",
    "ai-hub-gateway/gateway/routers/images.py",
    "ai-hub-gateway/gateway/routers/audio.py",
    "ai-hub-gateway/gateway/routers/video.py",
    "ai-hub-gateway/gateway/routers/status.py",
    "ai-hub-gateway/gateway/routers/voice.py",
    "ai-hub-gateway/gateway/routers/avatar.py",
    "ai-hub-gateway/gateway/routers/effects.py",
    "ai-hub-gateway/gateway/services/__init__.py",
    "ai-hub-gateway/gateway/services/ollama.py",
    "ai-hub-gateway/gateway/services/comfyui.py",
    "ai-hub-gateway/gateway/services/documusic.py",
    "ai-hub-gateway/gateway/services/wan2gp.py",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"  ERROR: {result.stderr}")
        return False
    return True


def main():
    print("=" * 60)
    print("  AI Hub Gateway v2.0 - Deploy to Server")
    print("=" * 60)

    # Step 1: Upload files via scp
    print("\n[1/3] Uploading files...")
    for filepath in FILES_TO_UPLOAD:
        local = os.path.join(BASE_DIR, filepath.replace("/", os.sep))
        remote = f"{SERVER}:{REMOTE_BASE}/{filepath}"
        dir_path = f"{REMOTE_BASE}/{os.path.dirname(filepath)}"
        run(f'ssh {SERVER} "mkdir -p {dir_path}"', check=False)

        if os.path.exists(local):
            if not run(f'scp "{local}" {remote}', check=False):
                print(f"  Skipped: {filepath}")
        else:
            print(f"  Not found: {local}")

    print("\n  All files uploaded!")

    # Step 2: Backup old gateway and swap
    print("\n[2/3] Swapping gateway on server...")
    swap_cmd = (
        f"ssh {SERVER} '"
        'if [ -d /mnt/seagate/ai-hub-gateway ]; then '
        "cp -r /mnt/seagate/ai-hub-gateway /mnt/seagate/ai-hub-gateway-v1-backup; "
        "echo Backed up v1; fi; "
        "rm -rf /mnt/seagate/ai-hub-gateway; "
        "cp -r /mnt/seagate/ai-hub-gateway-v2 /mnt/seagate/ai-hub-gateway; "
        "echo Installed v2; "
        "if [ -d /mnt/seagate/ai-hub-gateway-v1-backup/gateway/services ]; then "
        "for f in /mnt/seagate/ai-hub-gateway-v1-backup/gateway/services/*.py; do "
        "fname=$(basename $f); "
        "if [ ! -f /mnt/seagate/ai-hub-gateway/gateway/services/$fname ]; then "
        "cp $f /mnt/seagate/ai-hub-gateway/gateway/services/; echo Copied $fname; fi; done; fi; "
        "echo DONE'"
    )
    result = subprocess.run(swap_cmd, shell=True, capture_output=True, text=True)
    print(f"  {result.stdout.strip()}")

    # Step 3: Restart gateway
    print("\n[3/3] Restarting gateway service...")
    restart_cmd = (
        f"ssh {SERVER} '"
        "cd /mnt/seagate/ai-hub-gateway; "
        "pkill -f 'uvicorn.*main:app' 2>/dev/null || true; "
        "sleep 2; "
        "source /mnt/seagate/venvs/ai-hub-gateway/bin/activate 2>/dev/null || true; "
        "nohup python -m uvicorn main:app --host 0.0.0.0 --port 9000 > /tmp/gateway.log 2>&1 & "
        "sleep 3; "
        "curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/'"
    )
    result = subprocess.run(restart_cmd, shell=True, capture_output=True, text=True)
    status = result.stdout.strip()
    print(f"  Gateway HTTP status: {status}")

    if status == "200":
        print("\n  [OK] Gateway v2.0 deployed successfully!")
        print("  Endpoint: http://100.105.27.27:9000/v1")
        print("  Docs:     http://100.105.27.27:9000/docs")
    else:
        print(f"\n  [WARN] Gateway returned: {status}")
        print(f"  Check logs: ssh {SERVER} 'cat /tmp/gateway.log'")


if __name__ == "__main__":
    main()
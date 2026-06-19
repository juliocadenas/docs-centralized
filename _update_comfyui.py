"""Update ComfyUI frontend to latest version on NAB9."""
import paramiko

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run(client, cmd, timeout=120):
    print(f"  > {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    rc = stdout.channel.recv_exit_status()
    if out: print(out)
    if err: print(err)
    return rc

def main():
    print("=== Connecting to NAB9 ===")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)

    # Find ComfyUI installation
    print("\n=== Finding ComfyUI ===")
    run(client, "cat /etc/systemd/system/comfyui.service | grep -E 'WorkingDirectory|ExecStart'")

    # Check current version
    print("\n=== Current ComfyUI version ===")
    run(client, "cd /mnt/seagate/ComfyUI && git log --oneline -1 2>/dev/null || echo 'not a git repo'")

    # Update ComfyUI
    print("\n=== Updating ComfyUI ===")
    run(client, "cd /mnt/seagate/ComfyUI && git pull origin main 2>&1 || echo 'git pull failed'")

    # Update frontend dependencies and build
    print("\n=== Updating frontend ===")
    run(client, "cd /mnt/seagate/ComfyUI/web && npm install 2>&1")
    run(client, "cd /mnt/seagate/ComfyUI/web && npm run build 2>&1")

    # Restart ComfyUI
    print("\n=== Restarting ComfyUI ===")
    run(client, f"echo {PASS} | sudo -S systemctl restart comfyui", timeout=30)

    # Wait and check
    import time
    time.sleep(5)
    print("\n=== Verifying ===")
    run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8188/")

    client.close()
    print("\nDONE")

if __name__ == "__main__":
    main()
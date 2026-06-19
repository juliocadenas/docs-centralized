"""Update ComfyUI to latest version on NAB9."""
import paramiko, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
COMFYUI_DIR = "/home/pepe/ComfyUI"

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

    # Check if it's a git repo
    print("\n=== Checking ComfyUI git status ===")
    run(client, f"cd {COMFYUI_DIR} && git remote -v")
    run(client, f"cd {COMFYUI_DIR} && git log --oneline -1")

    # Stash any local changes and pull latest
    print("\n=== Pulling latest ComfyUI ===")
    run(client, f"cd {COMFYUI_DIR} && git stash")
    run(client, f"cd {COMFYUI_DIR} && git pull origin master", timeout=60)

    # Check new version
    print("\n=== New ComfyUI version ===")
    run(client, f"cd {COMFYUI_DIR} && git log --oneline -1")

    # Update frontend (ComfyUI uses its own update mechanism)
    print("\n=== Updating frontend ===")
    # ComfyUI builds frontend into web/ directory. The update script handles this.
    run(client, f"cd {COMFYUI_DIR} && ls web/")

    # Check if there's a frontend update mechanism
    run(client, f"cd {COMFYUI_DIR} && ls web_update/ 2>/dev/null || echo 'no web_update dir'")
    # Try refreshing the frontend
    run(client, f"cd {COMFYUI_DIR} && python -c \"import folder_paths; print('frontend:', folder_paths.frontend_version)\" 2>&1 || true")

    # Restart ComfyUI
    print("\n=== Restarting ComfyUI ===")
    run(client, f"echo {PASS} | sudo -S systemctl restart comfyui", timeout=30)

    time.sleep(5)
    print("\n=== Verifying ===")
    run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8188/")
    run(client, "curl -s http://localhost:8188/system_stats 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print('Version:', d.get('system',{}).get('comfyui_version','unknown'))\" 2>/dev/null || echo 'check manually'")

    client.close()
    print("\nDONE")

if __name__ == "__main__":
    main()
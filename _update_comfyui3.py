"""Update ComfyUI frontend package on NAB9."""
import paramiko, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
COMFYUI_DIR = "/home/pepe/ComfyUI"
VENV = "/home/pepe/comfyui_env"

def run(client, cmd, timeout=120):
    print(f"  > {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    rc = stdout.channel.recv_exit_status()
    if out: print(out.encode('ascii', errors='replace').decode())
    if err: print(err.encode('ascii', errors='replace').decode())
    return rc

def main():
    print("=== Connecting to NAB9 ===")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)

    # Check current frontend package version
    print("\n=== Checking frontend package ===")
    run(client, f"{VENV}/bin/pip show comfyui-frontend-package 2>/dev/null || echo 'not installed via pip'")

    # Check if web/ exists elsewhere
    print("\n=== Finding web/ directory ===")
    run(client, f"find {COMFYUI_DIR} -name 'index.html' -type f 2>/dev/null")
    run(client, f"{VENV}/bin/pip show comfyui-frontend-package 2>/dev/null | grep Location")

    # Update the frontend package
    print("\n=== Updating comfyui-frontend-package ===")
    run(client, f"{VENV}/bin/pip install --upgrade comfyui-frontend-package 2>&1", timeout=120)

    # Check new version
    print("\n=== New frontend package version ===")
    run(client, f"{VENV}/bin/pip show comfyui-frontend-package | grep -E 'Name|Version'")

    # Restart ComfyUI
    print("\n=== Restarting ComfyUI ===")
    run(client, f"echo {PASS} | sudo -S systemctl restart comfyui", timeout=30)

    time.sleep(6)
    print("\n=== Verifying ===")
    run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8188/")

    # Check the frontend version served
    run(client, "curl -s http://localhost:8188/versions/frontend 2>/dev/null || echo 'no versions endpoint'")

    client.close()
    print("\nDONE")

if __name__ == "__main__":
    main()
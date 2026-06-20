"""Deploy AI Hub Studio portal to NAB9 via SSH/SCP (paramiko)."""
import paramiko, os, sys

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
REMOTE_DIR = "/mnt/seagate/ai-hub-studio"
LOCAL_DIR = os.path.join(os.path.dirname(__file__), "out")

def ssh_exec(client, cmd):
    print(f"  > {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out)
    if err: print(err)
    return stdout.channel.recv_exit_status()

def upload_dir(sftp, local, remote):
    """Recursively upload directory."""
    try: sftp.stat(remote)
    except: sftp.mkdir(remote)
    for item in os.listdir(local):
        lpath = os.path.join(local, item)
        rpath = f"{remote}/{item}"
        if os.path.isdir(lpath):
            upload_dir(sftp, lpath, rpath)
        else:
            print(f"  UP {rpath}")
            sftp.put(lpath, rpath)

def main():
    print("=== Connecting to NAB9 ===")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()

    print("\n=== Uploading static files ===")
    # Create remote dir
    ssh_exec(client, f"mkdir -p {REMOTE_DIR}/out")
    upload_dir(sftp, LOCAL_DIR, f"{REMOTE_DIR}/out")

    # Upload Dockerfile and nginx.conf
    local_base = os.path.dirname(__file__)
    for f in ["Dockerfile", "nginx.conf"]:
        lpath = os.path.join(local_base, f)
        rpath = f"{REMOTE_DIR}/{f}"
        print(f"  UP {rpath}")
        sftp.put(lpath, rpath)
    sftp.close()

    print("\n=== Building Docker image ===")
    ssh_exec(client, f"cd {REMOTE_DIR} && docker stop ai-hub-studio 2>/dev/null; docker rm ai-hub-studio 2>/dev/null; true")
    rc = ssh_exec(client, f"cd {REMOTE_DIR} && docker build -t ai-hub-studio .")
    if rc != 0:
        print("ERROR: Docker build failed!")
        sys.exit(1)

    print("\n=== Starting container ===")
    rc = ssh_exec(client, "docker run -d --name ai-hub-studio --restart unless-stopped -p 3000:3000 ai-hub-studio")
    if rc != 0:
        print("ERROR: Docker run failed!")
        sys.exit(1)

    print("\n=== Verifying ===")
    ssh_exec(client, "sleep 2 && docker ps --filter name=ai-hub-studio && curl -s -o /dev/null -w '%{http_code}' http://localhost:3000")

    print(f"\nDONE Portal deployed at http://{HOST}:3000")
    client.close()

if __name__ == "__main__":
    main()
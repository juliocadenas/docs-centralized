"""
Deploy GPU semaphore changes to Madrid server via SSH/SCP.
Uses paramiko for password-based auth.
"""
import os
import sys

try:
    import paramiko
except ImportError:
    os.system(f"{sys.executable} -m pip install paramiko -q")
    import paramiko

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
BASE = os.path.dirname(os.path.abspath(__file__))

# Files to deploy: (local_path, remote_path)
FILES = [
    ("ai-hub-gateway/main.py",                          "/mnt/seagate/ai-hub-gateway/main.py"),
    ("ai-hub-gateway/gateway/gpu_manager.py",           "/mnt/seagate/ai-hub-gateway/gateway/gpu_manager.py"),
    ("ai-hub-gateway/gateway/routers/images.py",        "/mnt/seagate/ai-hub-gateway/gateway/routers/images.py"),
    ("ai-hub-gateway/gateway/routers/video.py",         "/mnt/seagate/ai-hub-gateway/gateway/routers/video.py"),
    ("ai-hub-gateway/gateway/routers/audio.py",         "/mnt/seagate/ai-hub-gateway/gateway/routers/audio.py"),
    ("ai-hub-gateway/gateway/routers/avatar.py",        "/mnt/seagate/ai-hub-gateway/gateway/routers/avatar.py"),
]

def main():
    print(f"🔌 Connecting to {USER}@{HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    sftp = ssh.open_sftp()
    print("✅ Connected!\n")

    # Upload files
    for local_rel, remote_path in FILES:
        local_path = os.path.join(BASE, local_rel.replace("/", os.sep))
        if not os.path.exists(local_path):
            print(f"  ⚠️  SKIP (not found): {local_rel}")
            continue
        sftp.put(local_path, remote_path)
        print(f"  ✅ Uploaded: {local_rel} → {remote_path}")

    sftp.close()

    # Restart gateway
    print("\n🔄 Restarting ai-hub-gateway service...")
    stdin, stdout, stderr = ssh.exec_command(f"echo '{PASS}' | sudo -S systemctl restart ai-hub-gateway 2>&1")
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    if output:
        print(f"   {output}")

    # Check status
    print("\n📊 Checking service status...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active ai-hub-gateway")
    status = stdout.read().decode().strip()
    print(f"   Status: {status}")

    if status == "active":
        print("\n✅ Gateway restarted successfully!")
        # Quick health check
        print("\n🏥 Health check...")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:9000/ 2>&1")
        result = stdout.read().decode().strip()
        print(f"   {result[:200]}")
    else:
        print("\n❌ Gateway failed to start! Checking logs...")
        stdin, stdout, stderr = ssh.exec_command(f"echo '{PASS}' | sudo -S journalctl -u ai-hub-gateway --no-pager -n 20 2>&1")
        logs = stdout.read().decode().strip()
        print(logs)

    ssh.close()
    print("\n🏁 Deploy complete!")


if __name__ == "__main__":
    main()
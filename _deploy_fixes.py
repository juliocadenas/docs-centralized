"""Deploy voice.py + effects.py fixes and restart gateway."""
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

FILES = [
    ("ai-hub-gateway/gateway/routers/voice.py",   "/mnt/seagate/ai-hub-gateway/gateway/routers/voice.py"),
    ("ai-hub-gateway/gateway/routers/effects.py", "/mnt/seagate/ai-hub-gateway/gateway/routers/effects.py"),
]

def main():
    print(f"[INFO] Connecting to {USER}@{HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    sftp = ssh.open_sftp()
    print("[OK] Connected!")

    for local_rel, remote_path in FILES:
        local_path = os.path.join(BASE, local_rel.replace("/", os.sep))
        if os.path.exists(local_path):
            sftp.put(local_path, remote_path)
            print(f"  [OK] {local_rel}")
        else:
            print(f"  [SKIP] {local_rel}")

    sftp.close()

    print("\n[INFO] Restarting gateway...")
    stdin, stdout, stderr = ssh.exec_command(f"echo '{PASS}' | sudo -S systemctl restart ai-hub-gateway 2>&1")
    stdout.channel.recv_exit_status()

    import time
    time.sleep(3)

    stdin, stdout, stderr = ssh.exec_command("systemctl is-active ai-hub-gateway")
    status = stdout.read().decode().strip()
    print(f"  Status: {status}")

    if status != "active":
        print("[FAIL] Gateway not active! Logs:")
        stdin, stdout, stderr = ssh.exec_command(f"echo '{PASS}' | sudo -S journalctl -u ai-hub-gateway --no-pager -n 20 2>&1")
        print(stdout.read().decode())

    ssh.close()
    print("[DONE]")


if __name__ == "__main__":
    main()
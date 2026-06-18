"""Upload and start effects services on NAB9 (Rembg, Real-ESRGAN, Higgsfield)"""
import paramiko, time, os

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=20)

    # SFTP the file
    sftp = c.open_sftp()
    sftp.put('effects_services.py', '/tmp/effects_services.py')
    sftp.close()
    print("Uploaded effects_services.py")

    # Kill old
    c.exec_command("pkill -f effects_services 2>/dev/null; sleep 1; true", timeout=5)

    # Start
    stdin, stdout, stderr = c.exec_command("nohup /home/pepe/comfyui_env/bin/python3 /tmp/effects_services.py > /tmp/effects_services.log 2>&1 & echo PID=$!", timeout=10)
    pid = stdout.read().decode().strip()
    print(f"PID: {pid}")
    time.sleep(4)

    # Verify ports
    for port in [8050, 8051, 8052]:
        stdin, stdout, stderr = c.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}", timeout=5)
        code = stdout.read().decode().strip()
        print(f"Port {port}: HTTP {code}")

    # Check log
    stdin, stdout, stderr = c.exec_command("head -5 /tmp/effects_services.log 2>/dev/null", timeout=5)
    log = stdout.read().decode().strip()
    if log: print(f"Log: {log[:300]}")

    c.close()
    print("Done!")

if __name__ == "__main__":
    main()
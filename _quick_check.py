"""Quick SSH connectivity check."""
import paramiko, socket

SERVER = "100.105.27.27"
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((SERVER, 22))
    sock.close()
    if result == 0:
        print("SSH port OPEN")
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        s.connect(SERVER, username="pepe", password="pepe1234", timeout=10)
        _, o, e = s.exec_command("systemctl status vram-watchdog 2>&1 | head -15; echo ===; journalctl -u vram-watchdog --no-pager -n 15 2>&1; echo ===; ls -la /usr/local/bin/vram-watchdog.sh 2>&1", timeout=15)
        print(o.read().decode())
        s.close()
    else:
        print(f"SSH port CLOSED (code {result})")
except Exception as ex:
    print(f"Error: {ex}")
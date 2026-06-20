"""Check if NAB9 is back after reboot + fsck."""
import paramiko, time, socket, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def is_reachable():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((HOST, 22))
        s.close()
        return True
    except:
        return False

print(f"Checking {HOST}:22...")
if not is_reachable():
    print("Server STILL DOWN - fsck running on 96% full disk (can take hours)")
    print("Check physically or via Tailscale IP")
    sys.exit(1)

print("Server UP! Connecting...")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd):
    try:
        full = f"echo '{PASS}' | sudo -S {cmd} 2>&1"
        _, o, e = c.exec_command(full, timeout=30)
        out = o.read().decode('utf-8', errors='replace')
        return out.replace("[sudo] contraseña para pepe: ", "").replace("[sudo] password for pepe: ", "")
    except Exception as ex:
        return f"(error: {ex})"

print("\n=== FILESYSTEM ===")
print(run("mount | grep ' / '"))
print(run("df -h / | tail -1"))
print(run("uptime"))

print("\n=== FS WRITABLE TEST ===")
result = run("echo OK > /tmp/rw_test && cat /tmp/rw_test && rm /tmp/rw_test && echo WRITABLE")
print(result)

print("\n=== SERVICIOS ===")
print(run("curl -s -o /dev/null -w 'Gateway:9000=%{http_code}\\n' http://localhost:9000/v1/status"))
print(run("curl -s -o /dev/null -w 'Ollama:11434=%{http_code}\\n' http://localhost:11434/api/tags"))
print(run("systemctl is-active ai-hub-gateway"))

print("\n=== OLLAMA MODELS ===")
print(run("ollama list"))

print("\n=== DOCKER ===")
print(run("docker ps --format '{{.Names}}: {{.Status}}'"))

c.close()
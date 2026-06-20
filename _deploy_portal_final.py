"""Deploy portal via Python http.server with logs on USB disk (bypass read-only /tmp)."""
import paramiko, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
REMOTE_DIR = "/mnt/seagate/ai-hub-studio"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=60):
    print(f"\n>>> {cmd}")
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode()
    err = e.read().decode()
    if out: print(out)
    if err: print("STDERR:", err[:500])
    return o.channel.recv_exit_status()

# 1. Kill any existing python http.server on 3001
print("=" * 60)
print("DEPLOY PORTAL EN :3001 (Python http.server)")
print("=" * 60)
run("pkill -f 'http.server.*3001' 2>/dev/null; true")

# 2. Start Python http.server from USB disk, log to USB disk
# Use cd to USB disk + redirect to USB disk (NOT /tmp)
run(f"""cd {REMOTE_DIR}/out && PYTHONUNBUFFERED=1 nohup python3 -m http.server 3001 --bind 0.0.0.0 > {REMOTE_DIR}/portal_3001.log 2>&1 &""")

# 3. Wait and verify
time.sleep(3)
run("ps aux | grep 'http.server.*3001' | grep -v grep")
run("curl -s -o /dev/null -w 'Portal :3001 = HTTP %{http_code}\\n' http://localhost:3001")
run("curl -s http://localhost:3001 | head -5")

# 4. Check if the content is the NEW build (should have our improved chat)
print("\n" + "=" * 60)
print("VERIFICANDO CONTENIDO DEL PORTAL")
print("=" * 60)
run(f"head -3 {REMOTE_DIR}/out/index.html")
run(f"ls -la {REMOTE_DIR}/out/index.html")

c.close()
print(f"\n{'=' * 60}")
print(f"PORTAL: http://{HOST}:3001")
print(f"Gateway: http://{HOST}:9000/v1/status")
print(f"{'=' * 60}")
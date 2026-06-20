"""Check if portal is running on 3001, if not start it with setsid to detach."""
import paramiko, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
REMOTE_DIR = "/mnt/seagate/ai-hub-studio"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=15):
    print(f"\n>>> {cmd}")
    try:
        _, o, e = c.exec_command(cmd, timeout=timeout)
        out = o.read().decode()
        err = e.read().decode()
        if out: print(out)
        if err: print("STDERR:", err[:300])
        return o.channel.recv_exit_status()
    except Exception as ex:
        print(f"  (timeout/error: {ex})")
        return -1

# 1. Check if portal already running on 3001
print("=" * 60)
print("¿PORTAL CORRIENDO EN :3001?")
print("=" * 60)
run("curl -s -o /dev/null -w 'HTTP %{http_code}\\n' http://localhost:3001")

# 2. Start with setsid + </dev/null to fully detach from SSH channel
# This prevents paramiko from hanging
print("\n" + "=" * 60)
print("INICIANDO PORTAL (setsid detach)")
print("=" * 60)
run(f"setsid bash -c 'cd {REMOTE_DIR}/out && python3 -m http.server 3001 --bind 0.0.0.0 >{REMOTE_DIR}/portal_3001.log 2>&1' </dev/null >/dev/null 2>&1 &", timeout=5)
time.sleep(4)

# 3. Verify
print("\n" + "=" * 60)
print("VERIFICACIÓN")
print("=" * 60)
run("curl -s -o /dev/null -w 'Portal :3001 = HTTP %{http_code}\\n' http://localhost:3001")
run("curl -s http://localhost:3001 | head -3")
run("ps aux | grep 'http.server.*3001' | grep -v grep | wc -l")

c.close()
print(f"\n{'=' * 60}")
print(f"PORTAL: http://{HOST}:3001")
print(f"{'=' * 60}")
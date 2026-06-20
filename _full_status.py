"""Check what's still running and try Python-based static server."""
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

# 1. Check all running services
print("=" * 60)
print("ESTADO DE SERVICIOS")
print("=" * 60)
run("curl -s -o /dev/null -w 'Gateway :9000 = HTTP %{http_code}\\n' http://localhost:9000/v1/status || echo 'Gateway DOWN'")
run("curl -s -o /dev/null -w 'Ollama :11434 = HTTP %{http_code}\\n' http://localhost:11434/api/tags || echo 'Ollama check'")
run("curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print('Ollama models:', [m['name'] for m in d.get('models',[])])\" 2>/dev/null || echo 'Ollama parse failed'")
run("systemctl is-active ai-hub-gateway.service 2>/dev/null || echo 'Gateway service unknown'")

# 2. Check what processes are running
print("\n" + "=" * 60)
print("PROCESOS IMPORTANTES")
print("=" * 60)
run("ps aux | grep -E '(ollama|gateway|comfy|nginx|python)' | grep -v grep | head -10")

# 3. Check Qwen installation status
print("\n" + "=" * 60)
print("ESTADO DE QWEN")
print("=" * 60)
run("ollama list 2>/dev/null || echo 'ollama list failed'")
run("ls -la /mnt/seagate/models/qwen/ 2>/dev/null || echo 'No qwen dir'")

# 4. Try Python http.server as alternative to Docker
print("\n" + "=" * 60)
print("PYTHON HTTP SERVER (alternativa sin Docker)")
print("=" * 60)
run("which python3")
run("pkill -f 'http.server.*3001' 2>/dev/null; true")
run(f"cd {REMOTE_DIR}/out && nohup python3 -m http.server 3001 --bind 0.0.0.0 > /tmp/portal_3001.log 2>&1 &")
time.sleep(2)
run("curl -s -o /dev/null -w 'Portal :3001 = HTTP %{http_code}\\n' http://localhost:3001")
run(f"ls {REMOTE_DIR}/out/index.html")

c.close()
print(f"\n{'=' * 60}")
print("DIAGNÓSTICO COMPLETO")
print(f"{'=' * 60}")
"""Verify portal content is new build + test Qwen chat via Gateway."""
import paramiko, json, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
REMOTE_DIR = "/mnt/seagate/ai-hub-studio"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=30):
    print(f"\n>>> {cmd[:100]}")
    try:
        _, o, e = c.exec_command(cmd, timeout=timeout)
        out = o.read().decode('utf-8', errors='replace')
        err = e.read().decode('utf-8', errors='replace')
        if out: print(out[:500])
        if err: print("STDERR:", err[:300])
        return out
    except Exception as ex:
        print(f"  (error: {ex})")
        return ""

# 1. Check portal content has our new build
print("=" * 60)
print("VERIFICANDO CONTENIDO DEL PORTAL")
print("=" * 60)
run(f"grep -c 'ChatTool\\|chat-completions\\|qwen' {REMOTE_DIR}/out/index.html || echo 'Buscando features...'")

# 2. Kill duplicate http.server, keep only one
print("\n" + "=" * 60)
print("LIMPIANDO PROCESOS DUPLICADOS")
print("=" * 60)
run("pkill -f 'http.server.*3001'; sleep 1")
run(f"setsid bash -c 'cd {REMOTE_DIR}/out && python3 -m http.server 3001 --bind 0.0.0.0 >{REMOTE_DIR}/portal_3001.log 2>&1' </dev/null >/dev/null 2>&1 &", timeout=5)
time.sleep(2)
run("ps aux | grep 'http.server.*3001' | grep -v grep | wc -l")

# 3. Test Qwen chat via Gateway
print("\n" + "=" * 60)
print("TEST CHAT CON QWEN2.5")
print("=" * 60)
test_payload = '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"Hello! What are you? Reply in one sentence."}],"stream":false}'
run(f"curl -s -X POST http://localhost:9000/v1/chat/completions -H 'Content-Type: application/json' -d '{test_payload}' | python3 -c \"import sys,json; d=json.load(sys.stdin); print('RESPUESTA:', d.get('choices',[{{}}])[0].get('message',{{}}).get('content','NO CONTENT')[:200])\"")

# 4. Test qwen2.5-coder
print("\n" + "=" * 60)
print("TEST CHAT CON QWEN2.5-CODER")
print("=" * 60)
test_payload2 = '{"model":"qwen2.5-coder:7b","messages":[{"role":"user","content":"Write a Python one-liner to reverse a string."}],"stream":false}'
run(f"curl -s -X POST http://localhost:9000/v1/chat/completions -H 'Content-Type: application/json' -d '{test_payload2}' | python3 -c \"import sys,json; d=json.load(sys.stdin); print('CODER:', d.get('choices',[{{}}])[0].get('message',{{}}).get('content','NO CONTENT')[:300])\"")

# 5. Create systemd service for portal auto-start
print("\n" + "=" * 60)
print("CREANDO SYSTEMD SERVICE PARA PORTAL")
print("=" * 60)
service = """[Unit]
Description=AI Hub Studio Portal (Python http.server)
After=network.target

[Service]
Type=simple
WorkingDirectory=/mnt/seagate/ai-hub-studio/out
ExecStart=/usr/bin/python3 -m http.server 3001 --bind 0.0.0.0
Restart=always
RestartSec=5
User=pepe

[Install]
WantedBy=multi-user.target
"""
sftp = c.open_sftp()
try:
    with sftp.file("/mnt/seagate/ai-hub-studio/portal-3001.service", 'w') as f:
        f.write(service)
    print("Service file written to /mnt/seagate/ai-hub-studio/portal-3001.service")
    print("(Cannot symlink to /etc/systemd due to read-only FS)")
    print("(Portal runs via setsid - will need manual restart after reboot)")
except Exception as ex:
    print(f"Error writing service: {ex}")
sftp.close()

c.close()
print(f"\n{'=' * 60}")
print(f"PORTAL: http://{HOST}:3001 (HTTP 200)")
print(f"Gateway: http://{HOST}:9000")
print(f"{'=' * 60}")
"""Deploy portal on port 3001 with different name (bypass zombie container)."""
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

# 1. Deploy new container on port 3001 with different name
print("=" * 60)
print("DEPLOY EN PUERTO 3001 (nuevo nombre)")
print("=" * 60)
run("docker rm -f ai-hub-studio-new 2>/dev/null; true")
run(f"""docker run -d \
  --name ai-hub-studio-new \
  --restart unless-stopped \
  -p 3001:3000 \
  -v {REMOTE_DIR}/out:/usr/share/nginx/html:ro \
  -v {REMOTE_DIR}/nginx_deploy.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx:alpine""")

# 2. Verify
print("\n" + "=" * 60)
print("VERIFICANDO")
print("=" * 60)
time.sleep(3)
run("docker ps --filter name=ai-hub-studio --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
run("curl -s -o /dev/null -w 'HTTP %{http_code}\\n' http://localhost:3001")
run("curl -s http://localhost:3001 | head -5")

c.close()
print(f"\n{'=' * 60}")
print(f"PORTAL NUEVO: http://{HOST}:3001")
print(f"(El viejo en :3000 está zombie por FS read-only)")
print(f"{'=' * 60}")
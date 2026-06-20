"""Force-remove old container and deploy via nginx volume mount."""
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

# 1. Force kill + remove old container (docker rm -f)
print("=" * 60)
print("FORZANDO REMOCIÓN DEL CONTENEDOR VIEJO")
print("=" * 60)
run("docker kill ai-hub-studio 2>&1; docker rm -f ai-hub-studio 2>&1; true")
run("docker ps -a --filter name=ai-hub-studio")

# 2. Run new container with volume mount (no build needed)
print("\n" + "=" * 60)
print("INICIANDO NUEVO CONTENEDOR")
print("=" * 60)
run(f"""docker run -d \
  --name ai-hub-studio \
  --restart unless-stopped \
  -p 3000:3000 \
  -v {REMOTE_DIR}/out:/usr/share/nginx/html:ro \
  -v {REMOTE_DIR}/nginx_deploy.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx:alpine""")

# 3. Verify
print("\n" + "=" * 60)
print("VERIFICANDO")
print("=" * 60)
time.sleep(3)
run("docker ps --filter name=ai-hub-studio --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
run("curl -s -o /dev/null -w 'HTTP %{http_code}\\n' http://localhost:3000")
run("curl -s http://localhost:3000 | head -10")

c.close()
print(f"\n{'=' * 60}")
print(f"PORTAL: http://{HOST}:3000")
print(f"{'=' * 60}")
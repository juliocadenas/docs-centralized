"""Deploy portal using nginx:alpine volume mount (no Docker build needed)."""
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

# 1. Verify /mnt/seagate is writable (USB disk - different from /)
print("=" * 60)
print("VERIFICANDO /mnt/seagate (USB)")
print("=" * 60)
run(f"touch {REMOTE_DIR}/test_write && echo 'WRITABLE' && rm {REMOTE_DIR}/test_write")

# 2. Create nginx config for serving the static files
print("\n" + "=" * 60)
print("CREANDO NGINX CONFIG")
print("=" * 60)
nginx_conf = """server {
    listen 3000;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri.html $uri/ /index.html;
    }

    location /_next/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
sftp = c.open_sftp()
with sftp.file(f"{REMOTE_DIR}/nginx_deploy.conf", 'w') as f:
    f.write(nginx_conf)
print(f"nginx config written to {REMOTE_DIR}/nginx_deploy.conf")

# 3. Stop old container, start new one with volume mount
print("\n" + "=" * 60)
print("REPLAZANDO CONTENEDOR")
print("=" * 60)
run("docker stop ai-hub-studio 2>/dev/null; docker rm ai-hub-studio 2>/dev/null; true")
run(f"""docker run -d \
  --name ai-hub-studio \
  --restart unless-stopped \
  -p 3000:3000 \
  -v {REMOTE_DIR}/out:/usr/share/nginx/html:ro \
  -v {REMOTE_DIR}/nginx_deploy.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx:alpine""")

# 4. Verify
print("\n" + "=" * 60)
print("VERIFICANDO")
print("=" * 60)
time.sleep(3)
run("docker ps --filter name=ai-hub-studio --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
run("curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000")
run("curl -s http://localhost:3000 | head -5")

sftp.close()
c.close()
print(f"\n{'=' * 60}")
print(f"PORTAL ACTUALIZADO: http://{HOST}:3000")
print(f"{'=' * 60}")
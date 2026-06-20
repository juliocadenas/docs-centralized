"""Clean Docker and retry portal deployment."""
import paramiko, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
REMOTE_DIR = "/mnt/seagate/ai-hub-studio"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=180):
    print(f"\n>>> {cmd}")
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode()
    err = e.read().decode()
    if out: print(out)
    if err: print("STDERR:", err)
    return o.channel.recv_exit_status()

# 1. Clean Docker build cache + unused images (libera ~75GB)
print("=" * 60)
print("LIMPIANDO DOCKER...")
print("=" * 60)
run("docker builder prune -af", timeout=120)
run("docker image prune -af", timeout=120)
run("docker container prune -f", timeout=60)
run("df -h / | tail -1")

# 2. Rebuild Docker image
print("\n" + "=" * 60)
print("REBUILD DOCKER IMAGE...")
print("=" * 60)
rc = run(f"cd {REMOTE_DIR} && docker build -t ai-hub-studio .", timeout=300)
if rc != 0:
    print("ERROR: Build failed again!")
    c.close()
    exit(1)

# 3. Stop old container and start new
print("\n" + "=" * 60)
print("RESTART CONTAINER...")
print("=" * 60)
run("docker stop ai-hub-studio 2>/dev/null; docker rm ai-hub-studio 2>/dev/null; true")
run("docker run -d --name ai-hub-studio --restart unless-stopped -p 3000:3000 ai-hub-studio")

# 4. Verify
print("\n" + "=" * 60)
print("VERIFICANDO...")
print("=" * 60)
time.sleep(3)
run("docker ps --filter name=ai-hub-studio --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
run("curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000")

c.close()
print(f"\n{'=' * 60}")
print(f"PORTAL: http://{HOST}:3000")
print(f"{'=' * 60}")
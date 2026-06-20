"""Check and fix read-only filesystem on NAB9."""
import paramiko

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

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

# 1. Check if / is actually read-only
print("=" * 60)
print("DIAGNÓSTICO FILESYSTEM")
print("=" * 60)
run("mount | grep 'on / '")
run("touch /tmp/test_write 2>&1 && echo 'WRITE OK' && rm /tmp/test_write || echo 'READ-ONLY CONFIRMED'")
run("dmesg | tail -20")

# 2. Check sudo access
print("\n" + "=" * 60)
print("VERIFICANDO SUDO")
print("=" * 60)
run("echo 'pepe1234' | sudo -S id 2>/dev/null || echo 'NO SUDO ACCESS'")

# 3. Try remount read-write
print("\n" + "=" * 60)
print("INTENTANDO REMOUNT RW")
print("=" * 60)
run("echo 'pepe1234' | sudo -S mount -o remount,rw / 2>&1")
run("touch /tmp/test_write2 2>&1 && echo 'WRITE OK NOW' && rm /tmp/test_write2 || echo 'STILL READ-ONLY'")

# 4. Check docker images already available
print("\n" + "=" * 60)
print("IMÁGENES DOCKER DISPONIBLES")
print("=" * 60)
run("docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'")

# 5. Check running containers
print("\n" + "=" * 60)
print("CONTENEDORES CORRIENDO")
print("=" * 60)
run("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")

c.close()
print("\nDONE")
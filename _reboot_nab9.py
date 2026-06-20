"""Reboot NAB9 to fix read-only filesystem, then wait for recovery and verify."""
import paramiko, time, socket

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def ssh_connect(timeout=10):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=timeout)
    return c

def run_cmd(c, cmd, timeout=30):
    print(f"\n>>> {cmd[:80]}")
    try:
        _, o, e = c.exec_command(cmd, timeout=timeout)
        out = o.read().decode('utf-8', errors='replace')
        err = e.read().decode('utf-8', errors='replace')
        if out: print(out[:600])
        if err: print("STDERR:", err[:300])
        return out
    except Exception as ex:
        print(f"  (error: {ex})")
        return ""

def is_reachable():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((HOST, 22))
        s.close()
        return True
    except:
        return False

# ==========================================
# FASE 1: PRE-REBOOT CHECK
# ==========================================
print("=" * 60)
print("FASE 1: ESTADO PRE-REBOOT")
print("=" * 60)
try:
    c = ssh_connect()
    run_cmd(c, "mount | grep ' / '")
    run_cmd(c, "df -h / | tail -1")
    run_cmd(c, "uptime")

    # ==========================================
    # FASE 2: PROGRAMAR FSCK + REBOOT
    # ==========================================
    print("\n" + "=" * 60)
    print("FASE 2: PROGRAMANDO FSCK + REBOOT")
    print("=" * 60)
    
    # Create auto-fsck trigger on USB disk first (writable)
    run_cmd(c, "sudo touch /forcefsck 2>&1 || echo 'Cannot touch /forcefsck (FS ro)'")
    
    # Try remount rw first (might work for /forcefsck)
    run_cmd(c, "sudo mount -o remount,rw / 2>&1 || echo 'Cannot remount (expected if heavy ro)'")
    run_cmd(c, "sudo touch /forcefsck 2>&1 || echo 'Still cannot create /forcefsck'")
    
    # Schedule fsck via tune2fs (persists in superblock)
    run_cmd(c, "sudo tune2fs -C 1 -c 1 /dev/sda3 2>&1 || sudo tune2fs -C 1 -c 1 /dev/nvme0n1p3 2>&1 || echo 'tune2fs failed (need disk name)'")
    
    # Check what disk is /
    run_cmd(c, "df / | tail -1")
    run_cmd(c, "lsblk | grep -E 'part|disk' | head -10")

    # ==========================================
    # FASE 3: REBOOT
    # ==========================================
    print("\n" + "=" * 60)
    print("FASE 3: REBOOT!")
    print("=" * 60)
    print("Enviando comando reboot...")
    try:
        run_cmd(c, "sudo reboot", timeout=5)
    except:
        pass  # Expected - connection drops on reboot
    
    c.close()
except Exception as ex:
    print(f"Pre-reboot connection error: {ex}")

# ==========================================
# FASE 4: ESPERAR A QUE VUELVA
# ==========================================
print("\n" + "=" * 60)
print("FASE 4: ESPERANDO RECOVERY (puede tardar 2-5 min)")
print("=" * 60)

# Wait for server to go down
print("\nEsperando que baje...", end=" ")
for i in range(30):
    if not is_reachable():
        print("DOWN ✓")
        break
    time.sleep(2)
    print(".", end="", flush=True)

# Wait for server to come back
print("\nEsperando que vuelva...", end=" ")
recovered = False
for i in range(90):  # Up to 3 minutes
    if is_reachable():
        # Wait extra for SSH to be ready
        time.sleep(10)
        try:
            c = ssh_connect(timeout=15)
            recovered = True
            print(" UP ✓")
            break
        except:
            pass
    time.sleep(2)
    print(".", end="", flush=True)

if not recovered:
    print("\n⚠️ El servidor no volvió en 3 minutos. Puede que el fsck esté corriendo (tarda más con disco lleno).")
    print("Reintenta manualmente: ssh pepe@100.105.27.27")
    exit(1)

# ==========================================
# FASE 5: POST-REBOOT VERIFICATION
# ==========================================
print("\n" + "=" * 60)
print("FASE 5: VERIFICACIÓN POST-REBOOT")
print("=" * 60)

run_cmd(c, "mount | grep ' / '")
run_cmd(c, "df -h / | tail -1")
run_cmd(c, "uptime")

print("\n--- SERVICIOS ---")
run_cmd(c, "curl -s -o /dev/null -w 'Gateway :9000 = HTTP %{http_code}\\n' http://localhost:9000/v1/status")
run_cmd(c, "curl -s -o /dev/null -w 'Ollama :11434 = HTTP %{http_code}\\n' http://localhost:11434/api/tags")
run_cmd(c, "systemctl is-active ai-hub-gateway.service")
run_cmd(c, "ollama list 2>/dev/null | head -5")

print("\n--- DOCKER ---")
run_cmd(c, "docker ps --format 'table {{.Names}}\t{{.Status}}' | head -10")
run_cmd(c, "docker info 2>/dev/null | grep -E 'Storage|Server Version' | head -3")

# Test FS is writable now
print("\n--- TEST ESCRITURA FS ---")
run_cmd(c, "echo 'test' > /tmp/fs_test.txt && cat /tmp/fs_test.txt && rm /tmp/fs_test.txt && echo 'FS WRITABLE ✓' || echo 'FS STILL READ-ONLY ✗'")

c.close()
print(f"\n{'=' * 60}")
print("REBOOT COMPLETO")
print(f"{'=' * 60}")
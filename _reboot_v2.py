"""Reboot NAB9 using sudo -S (password via stdin) to fix read-only filesystem."""
import paramiko, time, socket, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def ssh_connect(timeout=10):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=timeout)
    return c

def run_sudo(c, cmd, timeout=30):
    """Run sudo command with password piped via stdin."""
    print(f"\n>>> sudo {cmd[:70]}")
    try:
        # Use sudo -S to read password from stdin
        full_cmd = f"echo '{PASS}' | sudo -S {cmd} 2>&1"
        _, o, e = c.exec_command(full_cmd, timeout=timeout)
        out = o.read().decode('utf-8', errors='replace')
        err = e.read().decode('utf-8', errors='replace')
        combined = out + err
        # Filter out the sudo password prompt noise
        combined = combined.replace("[sudo] password for pepe: ", "").replace("Sorry, try again.", "")
        if combined.strip(): print(combined[:500])
        return combined
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
# CONECTAR Y PREPARAR
# ==========================================
print("=" * 60)
print("PREPARANDO REBOOT CON SUDO -S")
print("=" * 60)
c = ssh_connect()

# Test sudo works
print("\n--- TEST SUDO ---")
result = run_sudo(c, "whoami")
if "root" not in result:
    print("❌ SUDO NO FUNCIONA. No se puede hacer reboot automático.")
    print("⚠️  NECESITAS HACER REBOOT MANUAL:")
    print(f"   ssh {USER}@{HOST}")
    print(f"   Password: {PASS}")
    print("   sudo reboot")
    c.close()
    exit(1)
print("✅ Sudo OK")

# Program fsck
print("\n--- PROGRAMANDO FSCK ---")
run_sudo(c, "touch /forcefsck")
run_sudo(c, "tune2fs -C 1 -c 1 /dev/sda3")

# ==========================================
# REBOOT
# ==========================================
print("\n" + "=" * 60)
print("⚠️  EJECUTANDO REBOOT AHORA!")
print("=" * 60)
try:
    run_sudo(c, "reboot", timeout=5)
except:
    pass  # Connection drops
c.close()

# ==========================================
# ESPERAR
# ==========================================
print("\nEsperando que baje...", end=" ", flush=True)
for i in range(20):
    if not is_reachable():
        print("✓ DOWN")
        break
    time.sleep(2)
    print(".", end="", flush=True)

print("\nEsperando fsck + recovery (2-5 min)...", end=" ", flush=True)
recovered = False
for i in range(120):  # 4 minutes
    if is_reachable():
        time.sleep(15)
        try:
            c = ssh_connect(timeout=15)
            recovered = True
            print("✓ UP")
            break
        except:
            pass
    time.sleep(2)
    if i % 10 == 0: print(".", end="", flush=True)

if not recovered:
    print("\n⚠️  No volvió en 4 min. El fsck puede estar corriendo (disco 96% lleno).")
    print("Espera 5-10 min más y ejecuta: python _verify_reboot.py")
    exit(1)

# ==========================================
# VERIFICAR
# ==========================================
print("\n" + "=" * 60)
print("VERIFICACIÓN POST-REBOOT")
print("=" * 60)

run_sudo(c, "mount | grep ' / '")
result = run_sudo(c, "echo RW_TEST > /tmp/test_rw && cat /tmp/test_rw && rm /tmp/test_rw && echo FS_WRITABLE_OK")

if "FS_WRITABLE_OK" in result:
    print("\n🎉 FILESYSTEM WRITABLE! FSCK funcionó!")
else:
    print("\n⚠️  FS sigue read-only")

print("\n--- SERVICIOS ---")
run_sudo(c, "curl -s -o /dev/null -w 'Gateway:9000=%{http_code}\\n' http://localhost:9000/v1/status")
run_sudo(c, "curl -s -o /dev/null -w 'Ollama:11434=%{http_code}\\n' http://localhost:11434/api/tags")

print("\n--- DOCKER ---")
run_sudo(c, "docker ps --format '{{.Names}}: {{.Status}}' | head -5")

c.close()
print(f"\n{'=' * 60}")
print("✅ REBOOT + FSCK COMPLETO")
print(f"{'=' * 60}")
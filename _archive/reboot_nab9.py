#!/usr/bin/env python3
"""Regenerar initramfs + reboot + verificar."""
import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run_cmd(ssh, cmd, timeout=300):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=20)
    print("CONECTADO!\n")

    # 1. REGENERAR INITRAMFS
    print("=" * 60)
    print("1. REGENERANDO INITRAMFS")
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S update-initramfs -u -k all 2>&1", timeout=120)
    print(f"   {out.strip()[:500]}")
    print("   Initramfs regenerado")

    # 2. SINCRONIZAR
    print("\n" + "=" * 60)
    print("2. SINCRONIZANDO DISCOS")
    run_cmd(ssh, "sync", timeout=30)
    print("   sync completado")

    # 3. ESTADO PRE-REBOOT
    print("\n" + "=" * 60)
    print("3. ESTADO PRE-REBOOT")
    out, _ = run_cmd(ssh, """
echo "Uptime: $(uptime -p)"
echo "Autosuspend: $(cat /sys/module/usbcore/parameters/autosuspend)"
echo "Mount: $(mount | grep ' / ')"
docker ps --format '  {{.Names}}: {{.Status}}' 2>/dev/null
""")
    print(out)

    # 4. DETENER DOCKER
    print("=" * 60)
    print("4. DETENIENDO DOCKER")
    run_cmd(ssh, "echo pepe1234 | sudo -S systemctl stop docker docker.socket 2>&1", timeout=60)
    print("   Docker detenido")

    # 5. REBOOT
    print("\n" + "=" * 60)
    print("5. EJECUTANDO REBOOT...")
    print("   Esperando 90 segundos...\n")
    
    try:
        run_cmd(ssh, "echo pepe1234 | sudo -S systemctl reboot 2>&1", timeout=10)
    except:
        pass
    
    ssh.close()
    
    # 6. ESPERAR Y VERIFICAR
    print("   Esperando 90 segundos...")
    time.sleep(90)
    
    print("   Intentando reconectar...")
    for attempt in range(1, 6):
        try:
            ssh2 = paramiko.SSHClient()
            ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh2.connect(HOST, username=USER, password=PASS, timeout=15)
            print(f"\nSERVIDOR ARRANCO! (intento {attempt})\n")
            
            out, _ = run_cmd(ssh2, """
echo "=== POST-REBOOT ==="
echo "Uptime: $(uptime -p)"
echo ""
echo "=== /proc/cmdline ==="
cat /proc/cmdline
echo ""
echo "=== Autosuspend ==="
cat /sys/module/usbcore/parameters/autosuspend
echo ""
echo "=== Mount root ==="
mount | grep " / "
echo ""
echo "=== Docker ==="
systemctl is-active docker
echo ""
echo "=== USB errores ==="
dmesg | grep -ci "usb.*error\\|usb.*reset\\|usb.*disconnect" 2>/dev/null
echo ""
echo "=== Servicios ==="
docker ps --format '{{.Names}}: {{.Status}}' 2>/dev/null | head -5
echo ""
echo "=== Espacio ==="
df -h / | tail -1
""")
            print(out)
            
            ssh2.close()
            print("\nREBOOT EXITOSO!")
            return
            
        except Exception as e:
            print(f"   Intento {attempt}: no disponible ({str(e)[:60]})")
            time.sleep(20)
    
    print("\nEl servidor no respondio despues de 5 intentos.")
    print("Puede estar haciendo fsck. Verificar manualmente:")
    print("  ssh pepe@100.105.27.27")

if __name__ == "__main__":
    main()
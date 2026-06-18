#!/usr/bin/env python3
"""Arreglar mount read-only - quitar data=journal que no permite remount."""
import paramiko
import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run_cmd(ssh, cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=20)
    print("CONECTADO!\n")

    # ===== 1. Verificar estado actual =====
    print("=" * 60)
    print("1. ESTADO ACTUAL")
    out, _ = run_cmd(ssh, "mount | grep sda3")
    print(f"   {out.strip()}")

    # ===== 2. Editar fstab via SFTP (quitar data=journal) =====
    print("\n" + "=" * 60)
    print("2. ARREGLANDO FSTAB (quitar data=journal)")
    
    # Leer fstab
    out, _ = run_cmd(ssh, "cat /etc/fstab")
    fstab_content = out
    
    # Verificar si podemos escribir (probablemente no, es RO)
    # Intentar primero remontar RW sin data=journal
    
    # Primero intentamos remontar RW ignorando fstab
    print("   Intentando remount rw directo...")
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S mount -o remount,rw /dev/sda3 / 2>&1")
    print(f"   Resultado: {out.strip()}")
    if err.strip():
        err_clean = [l for l in err.split('\n') if 'contraseña' not in l and l.strip()]
        if err_clean:
            print(f"   err: {' '.join(err_clean)[:200]}")
    
    # Verificar
    out, _ = run_cmd(ssh, "mount | grep sda3")
    print(f"   Mount ahora: {out.strip()}")
    
    if 'ro,' in out:
        # Sigue RO, intentar otra estrategia
        print("\n   Sigue RO. Intentando con mount explícito...")
        out, err = run_cmd(ssh, "echo pepe1234 | sudo -S mount -o remount,rw /dev/sda3 2>&1")
        print(f"   Resultado: {out.strip()}")
        
        # Último intento: forzar
        out, err = run_cmd(ssh, "echo pepe1234 | sudo -S mount -f -o remount,rw / 2>&1")
        print(f"   Force: {out.strip()}")
        
        out, _ = run_cmd(ssh, "mount | grep sda3")
        print(f"   Mount: {out.strip()}")
    
    # Si ahora es RW, editar fstab
    out, _ = run_cmd(ssh, "mount | grep sda3")
    if 'rw,' in out or 'rw)' in out:
        print("\n   Sistema RW! Editando fstab...")
        
        # Quitar data=journal del fstab
        new_fstab = fstab_content.replace(
            "noatime,data=journal,commit=1,errors=remount-ro",
            "noatime,commit=1,errors=remount-ro"
        )
        
        # Escribir via SFTP
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/fstab.new", "w") as f:
            f.write(new_fstab)
        sftp.close()
        
        run_cmd(ssh, "echo pepe1234 | sudo -S cp /etc/fstab /etc/fstab.bak 2>&1")
        run_cmd(ssh, "echo pepe1234 | sudo -S cp /tmp/fstab.new /etc/fstab 2>&1")
        
        # Verificar
        out, _ = run_cmd(ssh, "grep ' / ' /etc/fstab")
        print(f"   Fstab nuevo: {out.strip()}")
        
        # ===== 3. Set journal_data via tune2fs (persistente en superblock) =====
        print("\n" + "=" * 60)
        print("3. SETTING journal_data VIA TUNE2FS (persistente)")
        print("   Esto hace que data=journal aplique en cada mount automáticamente")
        print("   sin necesidad de ponerlo en fstab (que causa el problema de remount)")
        
        out, err = run_cmd(ssh, "echo pepe1234 | sudo -S tune2fs -o journal_data /dev/sda3 2>&1")
        print(f"   {out.strip()}")
        if err.strip():
            err_clean = [l for l in err.split('\n') if 'contraseña' not in l and l.strip()]
            if err_clean:
                print(f"   err: {' '.join(err_clean)[:200]}")
        
        # Verificar
        out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S tune2fs -l /dev/sda3 2>/dev/null | grep -i 'default mount opts'")
        print(f"   Default mount opts: {out.strip()}")
        
        # ===== 4. Iniciar Docker =====
        print("\n" + "=" * 60)
        print("4. INICIANDO DOCKER")
        out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S systemctl start docker 2>&1", timeout=60)
        time.sleep(5)
        out, _ = run_cmd(ssh, "systemctl is-active docker")
        print(f"   Docker: {out.strip()}")
        
        out, _ = run_cmd(ssh, "docker ps --format '{{.Names}}: {{.Status}}' 2>/dev/null")
        print(f"   Containers:\n{out}")
        
        # ===== 5. RESUMEN =====
        print("\n" + "=" * 60)
        print("RESUMEN:")
        out, _ = run_cmd(ssh, """
echo "=== MOUNT ==="
mount | grep sda3
echo ""
echo "=== FSTAB ==="
grep ' / ' /etc/fstab
echo ""
echo "=== TUNE2FS ==="
echo pepe1234 | sudo -S tune2fs -l /dev/sda3 2>/dev/null | grep -i "default mount opts"
echo ""
echo "=== DOCKER ==="
systemctl is-active docker
docker ps --format '  {{.Names}}: {{.Status}}' 2>/dev/null
echo ""
echo "=== CMDLINE ==="
cat /proc/cmdline
echo ""
echo "=== AUTOSUSPEND ==="
cat /sys/module/usbcore/parameters/autosuspend
""")
        print(out)
    else:
        print("\n   No se pudo montar RW. Necesita fsck offline.")
        print("   Ejecutando fsck forzado...")
        out, err = run_cmd(ssh, "echo pepe1234 | sudo -S fsck.ext4 -fy /dev/sda3 2>&1", timeout=120)
        print(f"   {out.strip()[:500]}")
        
        # Intentar remount de nuevo
        run_cmd(ssh, "echo pepe1234 | sudo -S mount -o remount,rw / 2>&1")
        out, _ = run_cmd(ssh, "mount | grep sda3")
        print(f"   Mount después fsck: {out.strip()}")

    ssh.close()
    print("\nListo!")

if __name__ == "__main__":
    main()
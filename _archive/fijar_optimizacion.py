#!/usr/bin/env python3
"""Arreglar optimizaciones que fallaron - systemd-boot + fstab + backup."""
import paramiko
import os
import sys

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
    ssh.connect(HOST, port=22, username=USER, password=PASS, timeout=20)
    print("CONECTADO!\n")

    # ===== 1. SABER QUE BOOTLOADER USA =====
    print("=" * 60)
    print("1. DETECTANDO BOOTLOADER")
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S bootctl status 2>&1 | head -10")
    print(f"   {out.strip()}")

    out, _ = run_cmd(ssh, "ls /boot/efi/loader/entries/ 2>/dev/null")
    print(f"   Entradas: {out.strip()}")

    # ===== 2. CONFIGURAR KERNEL CMDLINE EN SYSTEMD-BOOT =====
    print("\n" + "=" * 60)
    print("2. CONFIGURANDO SYSTEMD-BOOT (Pop!_OS)")
    out, _ = run_cmd(ssh, "ls /boot/efi/loader/entries/ 2>/dev/null")
    entries = out.strip()

    if entries:
        for entry in entries.strip().split('\n'):
            entry = entry.strip()
            if not entry:
                continue
            out2, _ = run_cmd(ssh, f"cat '/boot/efi/loader/entries/{entry}' 2>/dev/null")
            print(f"\n   --- {entry} ---")
            print(f"   {out2.strip()}")

            if "options" in out2.lower():
                run_cmd(ssh, f"echo pepe1234 | sudo -S cp '/boot/efi/loader/entries/{entry}' '/boot/efi/loader/entries/{entry}.bak' 2>&1")
                run_cmd(ssh, f"""echo pepe1234 | sudo -S bash -c '
FILE="/boot/efi/loader/entries/{entry}"
if grep -q "usbcore.autosuspend" "$FILE"; then
    echo "Ya tiene autosuspend"
else
    sed -i "/^options/s/$/ usbcore.autosuspend=-1 usbcore.usbfs_memory_mb=0/" "$FILE"
    echo "autosuspend agregado"
fi
' 2>&1""")
                out3, _ = run_cmd(ssh, f"cat '/boot/efi/loader/entries/{entry}' 2>/dev/null | grep options")
                print(f"   Nuevo options: {out3.strip()}")

    # ===== 3. ARREGLAR FSTAB PARA data=journal =====
    print("\n" + "=" * 60)
    print("3. ARREGLANDO FSTAB")
    run_cmd(ssh, "echo pepe1234 | sudo -S cp /etc/fstab /etc/fstab.bak.optim 2>&1")
    out, _ = run_cmd(ssh, "cat /etc/fstab")

    new_fstab = out.replace("noatime,errors=remount-ro", "noatime,data=journal,commit=1,errors=remount-ro")

    if new_fstab != out:
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/fstab.new", "w") as f:
            f.write(new_fstab)
        sftp.close()
        run_cmd(ssh, "echo pepe1234 | sudo -S cp /tmp/fstab.new /etc/fstab 2>&1")
        print("   FSTAB MODIFICADO")
    else:
        print("   WARNING: noatime no encontrado, intentando otro approach")
        run_cmd(ssh, """echo pepe1234 | sudo -S sed -i 's/noatime,errors=remount-ro/noatime,data=journal,commit=1,errors=remount-ro/' /etc/fstab 2>&1""")

    out, _ = run_cmd(ssh, "grep ' / ' /etc/fstab | grep -v '^#'")
    print(f"   Root line: {out.strip()}")

    # ===== 4. ARREGLAR BACKUP SCRIPT =====
    print("\n" + "=" * 60)
    print("4. ARREGLANDO BACKUP SCRIPT")

    backup_content = '#!/bin/bash\n'
    backup_content += 'BACKUP_DIR="/mnt/seagate/system_backup"\n'
    backup_content += 'DATE=$(date +%Y%m%d)\n'
    backup_content += 'mkdir -p "$BACKUP_DIR"\n'
    backup_content += 'tar czf "$BACKUP_DIR/config_${DATE}.tar.gz" /etc/fstab /etc/systemd/system/ /etc/udev/rules.d/ /home/pepe/.bashrc 2>/dev/null\n'
    backup_content += 'dpkg --get-selections > "$BACKUP_DIR/packages_${DATE}.txt" 2>/dev/null\n'
    backup_content += 'smartctl -d sat -a /dev/sda > "$BACKUP_DIR/smart_${DATE}.txt" 2>/dev/null\n'
    backup_content += 'find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null\n'
    backup_content += 'find "$BACKUP_DIR" -name "*.txt" -mtime +7 -delete 2>/dev/null\n'

    sftp = ssh.open_sftp()
    with sftp.file("/tmp/system-backup.sh", "w") as f:
        f.write(backup_content)
    sftp.close()

    run_cmd(ssh, "echo pepe1234 | sudo -S cp /tmp/system-backup.sh /usr/local/bin/system-backup.sh && sudo chmod +x /usr/local/bin/system-backup.sh 2>&1")
    run_cmd(ssh, "echo pepe1234 | sudo -S bash /usr/local/bin/system-backup.sh 2>&1")

    out, _ = run_cmd(ssh, "ls -lh /mnt/seagate/system_backup/ 2>&1")
    print(f"   {out.strip()}")

    # ===== 5. RESUMEN =====
    print("\n" + "=" * 60)
    print("RESUMEN FINAL:")
    out, _ = run_cmd(ssh, """
echo "=== KERNEL CMDLINE ==="
cat /boot/efi/loader/entries/*.conf 2>/dev/null | grep -i options
echo ""
echo "=== FSTAB ==="
grep " / " /etc/fstab | grep -v "^#"
echo ""
echo "=== AUTOSUSPEND ==="
cat /sys/module/usbcore/parameters/autosuspend
echo ""
echo "=== BACKUP ==="
ls -lh /mnt/seagate/system_backup/ 2>/dev/null
echo ""
echo "=== ESPACIO ==="
df -h /dev/sda3
""")
    print(out)

    ssh.close()
    print("\n⚠️  REBOOT requerido para aplicar kernel cmdline + data=journal")

if __name__ == "__main__":
    main()
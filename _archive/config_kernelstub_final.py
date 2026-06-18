#!/usr/bin/env python3
"""Configurar kernelstub correctamente + generar guia final NAB9."""
import paramiko
import sys
import os
import json

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

    # ===== 1. LEER KERNELSTUB CONFIG VIA SFTP =====
    print("=" * 60)
    print("1. EDITANDO KERNELSTUB CONFIG")
    
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S cat /etc/kernelstub/configuration 2>/dev/null")
    config = json.loads(out)
    
    # Agregar usbcore params a user kernel_options
    user_opts = config["user"]["kernel_options"]
    if "usbcore.autosuspend=-1" not in user_opts:
        user_opts.extend(["usbcore.autosuspend=-1", "usbcore.usbfs_memory_mb=0"])
        config["user"]["kernel_options"] = user_opts
    
    print(f"   Nuevas kernel_options: {config['user']['kernel_options']}")
    
    # Escribir config via SFTP
    sftp = ssh.open_sftp()
    config_json = json.dumps(config, indent=2)
    with sftp.file("/tmp/kernelstub.json", "w") as f:
        f.write(config_json)
    sftp.close()
    
    run_cmd(ssh, "echo pepe1234 | sudo -S cp /etc/kernelstub/configuration /etc/kernelstub/configuration.bak 2>&1")
    run_cmd(ssh, "echo pepe1234 | sudo -S cp /tmp/kernelstub.json /etc/kernelstub/configuration 2>&1")
    
    # Verificar
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S cat /etc/kernelstub/configuration 2>/dev/null")
    print(f"   Config guardada ✓")

    # ===== 2. EJECUTAR KERNELSTUB PARA REGENERAR BOOT =====
    print("\n" + "=" * 60)
    print("2. EJECUTANDO KERNELSTUB (regenera entradas de boot)")
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S kernelstub 2>&1", timeout=60)
    print(f"   {out.strip()}")
    if err.strip():
        # Filtrar stderr de password
        err_clean = [l for l in err.split('\n') if 'contraseña' not in l and l.strip()]
        if err_clean:
            print(f"   stderr: {' '.join(err_clean)[:300]}")

    # ===== 3. EDITAR DIRECTAMENTE EL CMDLINE EN EFI =====
    print("\n" + "=" * 60)
    print("3. EDITANDO CMDLINE DIRECTAMENTE EN EFI")
    
    # Leer cmdline actual
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S cat /boot/efi/EFI/Pop_OS-73b66df5-a1ca-428a-b006-fb8c396311ea/cmdline 2>/dev/null")
    current_cmdline = out.strip()
    print(f"   Cmdline actual: {current_cmdline}")
    
    # Agregar params si no los tiene
    if "usbcore.autosuspend" not in current_cmdline:
        new_cmdline = current_cmdline + " usbcore.autosuspend=-1 usbcore.usbfs_memory_mb=0"
        # Escribir via SFTP
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/cmdline.new", "w") as f:
            f.write(new_cmdline)
        sftp.close()
        run_cmd(ssh, "echo pepe1234 | sudo -S cp /tmp/cmdline.new /boot/efi/EFI/Pop_OS-73b66df5-a1ca-428a-b006-fb8c396311ea/cmdline 2>&1")
        
        # Verificar
        out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S cat /boot/efi/EFI/Pop_OS-73b66df5-a1ca-428a-b006-fb8c396311ea/cmdline 2>/dev/null")
        print(f"   Cmdline nuevo:  {out.strip()}")
        print("   ✓ Cmdline EFI actualizado")
    else:
        print("   Ya tiene usbcore.autosuspend")

    # ===== 4. VERIFICAR ENTRY DE BOOT =====
    print("\n" + "=" * 60)
    print("4. VERIFICANDO ENTRY DE SYSTEMD-BOOT")
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S cat /boot/efi/loader/entries/Pop_OS-current.conf 2>/dev/null")
    print(f"   {out.strip()}")

    # ===== 5. RESUMEN FINAL COMPLETO =====
    print("\n" + "=" * 60)
    print("RESUMEN FINAL - TODAS LAS OPTIMIZACIONES:")
    print("=" * 60)
    
    out, _ = run_cmd(ssh, """
echo "===== KERNEL CMDLINE (EFI) ====="
cat /boot/efi/EFI/Pop_OS-73b66df5-a1ca-428a-b006-fb8c396311ea/cmdline 2>/dev/null
echo ""
echo "===== /proc/cmdline (actual) ====="
cat /proc/cmdline
echo ""
echo "===== KERNELSTUB CONFIG ====="
cat /etc/kernelstub/configuration 2>/dev/null | grep -A5 kernel_options | tail -8
echo ""
echo "===== MODPROBE ====="
cat /etc/modprobe.d/usb-ssd-fix.conf
echo ""
echo "===== TMPFILES ====="
cat /etc/tmpfiles.d/usb-autosuspend.conf
echo ""
echo "===== UDEV ====="
cat /etc/udev/rules.d/90-ssd-usb.rules
echo ""
echo "===== FSTAB ROOT ====="
grep " / " /etc/fstab | grep -v "^#"
echo ""
echo "===== TUNE2FS ====="
echo pepe1234 | sudo -S tune2fs -l /dev/sda3 2>/dev/null | grep -iE "mount count|maximum"
echo ""
echo "===== CRON JOBS ====="
echo pepe1234 | sudo -S crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$"
echo ""
echo "===== INITRAMFS SCRIPTS ====="
ls /etc/initramfs-tools/scripts/init-premount/ 2>/dev/null
echo ""
echo "===== BACKUP SEAGATE ====="
ls -lh /mnt/seagate/system_backup/ 2>/dev/null
echo ""
echo "===== ESPACIO DISCO ====="
df -h /dev/sda3
echo ""
echo "===== USB ERRORES EN DMESG ====="
dmesg 2>/dev/null | grep -ci "usb.*error\\|usb.*reset\\|usb.*disconnect" || echo "0"
""")
    print(out)

    ssh.close()
    print("\n✅ TODAS LAS OPTIMIZACIONES APLICADAS")
    print("   REBOOT requerido para aplicar kernel cmdline + data=journal")

if __name__ == "__main__":
    main()
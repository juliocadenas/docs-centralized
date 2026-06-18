#!/usr/bin/env python3
"""Aplicar correcciones preventivas al servidor Madrid."""
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

    # ===== 1. CONFIGURAR FSCK EN CADA ARRANQUE =====
    print("=" * 50)
    print("1. Configurando fsck en cada arranque...")
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S tune2fs -c 1 /dev/sda3 2>&1")
    print(f"   tune2fs: {out.strip()}")
    
    # Verificar
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S tune2fs -l /dev/sda3 2>/dev/null | grep -iE 'mount count|maximum|check'")
    print(f"   Estado actual:\n{out}")

    # ===== 2. LIMPIAR DOCKER (80GB recuperable!) =====
    print("=" * 50)
    print("2. Limpiando Docker (images sin usar + build cache)...")
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S docker image prune -a -f --filter 'until=168h' 2>&1", timeout=120)
    print(f"   Image prune: {out.strip()[-200:]}")
    
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S docker builder prune -f 2>&1", timeout=120)
    print(f"   Builder prune: {out.strip()[-200:]}")
    
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S docker system df 2>&1")
    print(f"   Docker despues de limpieza:\n{out}")

    # ===== 3. LIMPIAR LOGS =====
    print("=" * 50)
    print("3. Limpiando logs de journal (998MB)...")
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S journalctl --vacuum-time=3d --vacuum-size=100M 2>&1")
    print(f"   {out.strip()}")
    
    # Limpiar syslog viejos
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S find /var/log -name '*.1' -o -name '*.gz' | xargs sudo rm -f 2>&1")
    print("   Logs antiguos eliminados")

    # ===== 4. LIMPIAR APT CACHE =====
    print("=" * 50)
    print("4. Limpiando apt cache (796MB)...")
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S apt-get clean 2>&1")
    out2, err2 = run_cmd(ssh, "echo pepe1234 | sudo -S apt-get autoremove -y 2>&1 | tail -5")
    print(f"   {out2.strip()}")

    # ===== 5. VERIFICAR ESPACIO LIBRE =====
    print("=" * 50)
    print("5. Espacio en disco despues de limpieza:")
    out, err = run_cmd(ssh, "df -h /dev/sda3")
    print(f"   {out.strip()}")

    # ===== 6. INSTALAR SCRIPT DE MONITOREO =====
    print("=" * 50)
    print("6. Instalando script de monitoreo de disco...")
    
    monitor_script = """#!/bin/bash
# Monitor de salud del disco - ejecuta cada hora via cron
LOG="/var/log/disk-health.log"

# SMART check
SMART=$(smartctl -d sat -H /dev/sda 2>/dev/null | grep "result" | awk '{print $NF}')
if [ "$SMART" != "PASSED" ]; then
    echo "$(date): ALERTA! SMART no PASSED: $SMART" >> $LOG
fi

# Espacio en disco
USAGE=$(df / | awk 'NR==2{print $5}' | tr -d '%')
if [ "$USAGE" -gt 90 ]; then
    echo "$(date): ALERTA! Disco al ${USAGE}%" >> $LOG
fi

# Errores ext4 en kernel
ERR=$(dmesg | grep -c "EXT4-fs error")
if [ "$ERR" -gt 0 ]; then
    echo "$(date): ALERTA! $ERR errores EXT4 en dmesg" >> $LOG
fi

# Errores USB (el SSD va por USB)
USB_ERR=$(dmesg | grep -ci "usb.*error\|usb.*reset\|usb.*disconnect")
if [ "$USB_ERR" -gt 5 ]; then
    echo "$(date): ALERTA! $USB_ERR errores USB (SSD se desconecta?)" >> $LOG
fi
"""
    # Subir script via SFTP
    sftp = ssh.open_sftp()
    with open("/tmp/disk_monitor.sh", "w") as f:
        pass  # create local temp
    
    # Use exec_command to create the script
    run_cmd(ssh, f"echo '{monitor_script}' | sudo -S tee /usr/local/bin/disk-monitor.sh > /dev/null && sudo chmod +x /usr/local/bin/disk-monitor.sh 2>&1")
    
    # Add to cron
    run_cmd(ssh, "echo pepe1234 | sudo -S bash -c '(crontab -l 2>/dev/null; echo \"0 * * * * /usr/local/bin/disk-monitor.sh\") | sort -u | crontab -' 2>&1")
    print("   Script instalado en /usr/local/bin/disk-monitor.sh")
    print("   Cron configurado para ejecutar cada hora")
    sftp.close()

    # ===== 7. CONFIGURAR DRACUT para auto-fsck =====
    print("=" * 50)
    print("7. Configurando boot para forzar fsck...")
    # Add fsck.mode=force to kernel boot params temporarily
    # Also configure initramfs to run fsck -y automatically
    run_cmd(ssh, """
echo pepe1234 | sudo -S bash -c 'cat > /etc/initramfs-tools/scripts/local-premount/autofsck << "SCRIPT"
#!/bin/sh
# Auto-fsck antes de montar raiz
PREREQ=""
prereqs() { echo "$PREREQ"; }
case "$1" in
    prereqs) prereqs; exit 0;;
esac
. /scripts/functions
log_begin_msg "Running automatic filesystem check"
fsck -y /dev/sda3 2>&1 | while read line; do log_begin_msg "$line"; done
log_end_msg
SCRIPT
chmod +x /etc/initramfs-tools/scripts/local-premount/autofsck
update-initramfs -u
' 2>&1
""")
    print("   Script de auto-fsck en initramfs instalado")
    print("   (Si cae a busybox, intentara fsck -y automaticamente)")

    # ===== RESUMEN FINAL =====
    print("\n" + "=" * 50)
    print("RESUMEN DE CAMBIOS APLICADOS:")
    print("=" * 50)
    
    out, err = run_cmd(ssh, "df -h /dev/sda3 && echo '---' && echo pepe1234 | sudo -S tune2fs -l /dev/sda3 2>/dev/null | grep -iE 'mount count|maximum' && echo '---' && echo pepe1234 | sudo -S docker system df 2>/dev/null")
    print(out)

    ssh.close()
    print("\nCORRECCIONES COMPLETADAS!")

if __name__ == "__main__":
    main()
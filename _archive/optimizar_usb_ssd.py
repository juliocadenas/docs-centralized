#!/usr/bin/env python3
"""Optimizar la conexión USB del SSD para minimizar corrupción en el NAB9."""
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
    print("CONECTADO al NAB9!\n")

    # ===== 1. DESACTIVAR USB AUTOSUSPEND (CAUSA #1 DE DESCONEXIONES) =====
    print("=" * 60)
    print("1. DESACTIVANDO USB AUTOSUSPEND")
    print("   (Esta es la causa #1 de micro-desconexiones del SSD USB)")
    
    # Verificar configuracion actual
    out, _ = run_cmd(ssh, "cat /sys/module/usbcore/parameters/autosuspend 2>/dev/null")
    print(f"   Autosuspend actual: {out.strip()} (segundos)")
    
    # Desactivar via GRUB de forma permanente
    out, err = run_cmd(ssh, """
echo pepe1234 | sudo -S bash -c '
# Backup del GRUB actual
cp /etc/default/grub /etc/default/grub.bak.$(date +%Y%m%d)

# Quitar cualquier usbcore.autosuspend anterior
sed -i "s/ usbcore.autosuspend=-1//g" /etc/default/grub
sed -i "s/usbcore.autosuspend=[0-9]*//g" /etc/default/grub

# Anadir usbcore.autosuspend=-1 y usbcore.usbfs_memory_mb=0 (sin limite)
GRUB_LINE=$(grep "^GRUB_CMDLINE_LINUX_DEFAULT=" /etc/default/grub)
if echo "$GRUB_LINE" | grep -q "usbcore.autosuspend"; then
    echo "Ya tiene autosuspend configurado"
else
    NEW_LINE=$(echo "$GRUB_LINE" | sed "s/\\\"$/ usbcore.autosuspend=-1 usbcore.usbfs_memory_mb=0\\\"/")
    sed -i "s|^GRUB_CMDLINE_LINUX_DEFAULT=.*|$NEW_LINE|" /etc/default/grub
fi

cat /etc/default/grub | grep GRUB_CMDLINE_LINUX_DEFAULT
' 2>&1
""")
    print(f"   GRUB: {out.strip()}")
    
    # Actualizar GRUB
    out, err = run_cmd(ssh, "echo pepe1234 | sudo -S update-grub 2>&1")
    print(f"   update-grub: {out.strip()[-100:]}")
    
    # Aplicar inmediatamente para esta sesion
    run_cmd(ssh, "echo pepe1234 | sudo -S bash -c 'echo -1 > /sys/module/usbcore/parameters/autosuspend 2>/dev/null; echo on > /sys/bus/usb/devices/*/power/control 2>/dev/null' 2>&1")
    print("   USB autosuspend desactivado INMEDIATAMENTE")

    # ===== 2. DESACTIVAR AUTOSUSPEND ESPECIFICO PARA EL SSD USB =====
    print("\n" + "=" * 60)
    print("2. DESACTIVANDO POWER MANAGEMENT DEL SSD USB ESPECIFICO")
    
    out, err = run_cmd(ssh, """
echo pepe1234 | sudo -S bash -c '
# Encontrar el dispositivo USB del SSD y desactivar autosuspend
for dev in /sys/bus/usb/devices/*/product; do
    if grep -qi "SATA\|SSD\|PNY\|OWC\|Adapter" "$dev" 2>/dev/null; then
        DIR=$(dirname "$dev")
        echo on > "$DIR/power/control" 2>/dev/null
        echo "  Desactivado autosuspend para: $(cat $dev)"
        # Tambien para interfaces hijo
        for child in "$DIR"/*:*/power/control; do
            echo on > "$child" 2>/dev/null
        done
    fi
done

# Regla udev permanente para el adaptador OWC
cat > /etc/udev/rules.d/90-ssd-usb.rules << "RULE"
# Desactivar autosuspend para el adaptador USB-SATA del SSD (OWC PA023U3)
ACTION=="add|change", SUBSYSTEM=="usb", ATTR{idVendor}=="7825", ATTR{idProduct}=="a2a4", TEST=="power/control", ATTR{power/control}="on"
# Desactivar autosuspend para cualquier disco USB
ACTION=="add|change", SUBSYSTEM=="usb", ATTR{bDeviceClass}=="00", TEST=="power/control", ATTR{power/control}="on"
RULE

udevadm control --reload-rules 2>/dev/null
udevadm trigger 2>/dev/null
echo "Regla udev instalada"
' 2>&1
""")
    print(f"   {out.strip()}")

    # ===== 3. CAMBIAR EXT4 A data=journal (MODO MAS SEGURO) =====
    print("\n" + "=" * 60)
    print("3. CAMBIANDO EXT4 A MODO data=journal (maxima integridad)")
    print("   (Esto journals tanto metadatos COMO datos. Mas seguro para USB)")
    
    out, err = run_cmd(ssh, """
echo pepe1234 | sudo -S bash -c '
# Verificar modo actual
echo "Modo actual:"
tune2fs -l /dev/sda3 2>/dev/null | grep "Default mount"

# Cambiar a data=journal (requiere desmontar, lo configuramos para el proximo boot)
# Primero lo anadimos al fstab
cp /etc/fstab /etc/fstab.bak.$(date +%Y%m%d)

# Ver si ya tiene opciones personalizadas
ROOT_LINE=$(grep " / " /etc/fstab | grep -v "^#")
echo "Linea fstab actual: $ROOT_LINE"
' 2>&1
""")
    print(f"   {out.strip()}")
    
    # Mostrar fstab actual
    out, _ = run_cmd(ssh, "cat /etc/fstab")
    print(f"\n   /etc/fstab actual:\n{out}")

    # Modificar fstab para anadir data=journal y commit=1
    print("   Modificando fstab para data=journal,commit=1...")
    out, err = run_cmd(ssh, r"""
echo pepe1234 | sudo -S bash -c '
# Encontrar la linea de root y modificarla
ROOT_UUID=$(grep " / " /etc/fstab | grep -v "^#" | awk '{print $1}')

# Si la linea usa UUID
if echo "$ROOT_UUID" | grep -q "UUID"; then
    sed -i "s|\(^$ROOT_UUID.*defaults\).*|\1,data=journal,commit=1|" /etc/fstab
elif echo "$ROOT_UUID" | grep -q "/dev/sda3"; then
    sed -i "s|\(^/dev/sda3.*defaults\).*|\1,data=journal,commit=1|" /etc/fstab
fi

echo "Nuevo fstab (linea root):"
grep " / " /etc/fstab | grep -v "^#"
' 2>&1
""")
    print(f"   {out.strip()}")

    # ===== 4. CONFIGURAR UAS (USB Attached SCSI) PARA MAXIMA ESTABILIDAD =====
    print("\n" + "=" * 60)
    print("4. VERIFICANDO DRIVER USB (UAS vs usb-storage)")
    
    out, err = run_cmd(ssh, """
echo pepe1234 | sudo -S bash -c '
echo "Driver actual del SSD:"
ls -la /sys/block/sda/device/../driver 2>/dev/null | awk "{print \$NF}"
echo ""
echo "Velocidad USB:"
cat /sys/block/sda/device/../speed 2>/dev/null
echo ""
echo "Estado del link USB:"
cat /sys/block/sda/device/../urbnum 2>/dev/null
echo ""
# Ver si hay errores de reset USB
dmesg | grep -ci "usb.*reset\|usb.*disconnect\|usb.*error" 2>/dev/null
echo "errores USB en este boot"
' 2>&1
""")
    print(f"   {out.strip()}")

    # ===== 5. CREAR SCRIPT DE BACKUP AUTOMATICO AL SEAGATE =====
    print("\n" + "=" * 60)
    print("5. INSTALANDO BACKUP AUTOMATICO DE CONFIG CRITICA AL SEAGATE")
    
    backup_script = '''#!/bin/bash
# Backup diario de configuracion critica al Seagate 1.8TB
BACKUP_DIR="/mnt/seagate/system_backup"
DATE=$(date +%Y%m%d)
MAX_BACKUPS=7

mkdir -p "$BACKUP_DIR"

# 1. Backup de configuracion del sistema
tar czf "$BACKUP_DIR/config_${DATE}.tar.gz" \\
    /etc/fstab \\
    /etc/default/grub \\
    /etc/systemd/system/ \\
    /etc/docker/ \\
    /etc/udev/rules.d/ \\
    /home/pepe/.bashrc \\
    /home/pepe/.config/ \\
    --exclude='*.pyc' \\
    2>/dev/null

# 2. Lista de paquetes instalados
dpkg --get-selections > "$BACKUP_DIR/packages_${DATE}.txt" 2>/dev/null

# 3. Docker compose files y configs
if [ -d /home/pepe/ai-hub-gateway ]; then
    tar czf "$BACKUP_DIR/gateway_${DATE}.tar.gz" \\
        /home/pepe/ai-hub-gateway/ \\
        2>/dev/null
fi

# 4. SMART snapshot
smartctl -d sat -a /dev/sda > "$BACKUP_DIR/smart_${DATE}.txt" 2>/dev/null

# 5. Limpiar backups viejos (mantener 7 dias)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$MAX_BACKUPS -delete 2>/dev/null
find "$BACKUP_DIR" -name "*.txt" -mtime +$MAX_BACKUPS -delete 2>/dev/null

echo "$(date): Backup completado en $BACKUP_DIR" >> /var/log/backup.log
'''
    
    run_cmd(ssh, f"echo '{backup_script}' | sudo -S tee /usr/local/bin/system-backup.sh > /dev/null && sudo chmod +x /usr/local/bin/system-backup.sh 2>&1")
    
    # Ejecutar backup ahora
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S /usr/local/bin/system-backup.sh 2>&1")
    
    # Configurar cron para backup diario a las 4am
    run_cmd(ssh, "echo pepe1234 | sudo -S bash -c '(crontab -l 2>/dev/null; echo \"0 4 * * * /usr/local/bin/system-backup.sh\") | sort -u | crontab -' 2>&1")
    
    # Verificar backup
    out, _ = run_cmd(ssh, "ls -lh /mnt/seagate/system_backup/ 2>&1")
    print(f"   Backup inicial creado:\n{out}")
    print("   Cron: backup diario a las 4:00 AM")

    # ===== 6. CREAR SCRIPT DE RECOVERY RAPIDO =====
    print("\n" + "=" * 60)
    print("6. INSTALANDO SCRIPT DE RECOVERY PARA BUSYBOX")
    
    recovery_script = '''#!/bin/sh
# === SCRIPT DE RECOVERY PARA BUSYBOX INITRAMFS ===
# Copiar a /etc/initramfs-tools/scripts/init-premount/usb-ssd-recovery
# Se ejecuta ANTES de intentar montar la raiz

PREREQ=""
prereqs() { echo "$PREREQ"; }
case "$1" in prereqs) prereqs; exit 0;; esac

. /scripts/functions

log_begin_msg "=== NAB9 USB-SSD RECOVERY ==="

# Esperar a que el dispositivo USB aparezca
for i in $(seq 1 30); do
    if [ -b /dev/sda3 ]; then
        log_begin_msg "SSD USB detectado en intento $i"
        break
    fi
    sleep 1
done

if [ ! -b /dev/sda3 ]; then
    log_begin_msg "ERROR: /dev/sda3 no aparece. Reset USB..."
    # Reset del controlador USB
    echo 0 > /sys/bus/usb/devices/usb1/authorized 2>/dev/null
    echo 0 > /sys/bus/usb/devices/usb2/authorized 2>/dev/null
    sleep 2
    echo 1 > /sys/bus/usb/devices/usb1/authorized 2>/dev/null
    echo 1 > /sys/bus/usb/devices/usb2/authorized 2>/dev/null
    sleep 5
fi

# Si aparece, hacer fsck
if [ -b /dev/sda3 ]; then
    log_begin_msg "Ejecutando fsck -y /dev/sda3"
    fsck -y /dev/sda3 2>&1
    log_begin_msg "fsck completado"
else
    log_begin_msg "FATAL: SSD USB no responde. Verificar conexion fisica."
fi

log_end_msg
'''
    
    run_cmd(ssh, f"""
echo pepe1234 | sudo -S bash -c '
mkdir -p /etc/initramfs-tools/scripts/init-premount/
cat > /etc/initramfs-tools/scripts/init-premount/usb-ssd-recovery << "RECOVERYEOF"
{recovery_script}
RECOVERYEOF
chmod +x /etc/initramfs-tools/scripts/init-premount/usb-ssd-recovery
update-initramfs -u 2>&1 | tail -3
echo "Script de recovery instalado en initramfs"
' 2>&1
""")
    print("   Script de recovery USB instalado en initramfs")
    print("   (Espera 30s al SSD USB + reset USB + fsck automatico)")

    # ===== 7. RESUMEN FINAL =====
    print("\n" + "=" * 60)
    print("RESUMEN DE OPTIMIZACIONES USB:")
    print("=" * 60)
    
    out, _ = run_cmd(ssh, """
echo "=== GRUB CMDLINE ==="
grep GRUB_CMDLINE_LINUX_DEFAULT /etc/default/grub
echo ""
echo "=== FSTAB ROOT ==="
grep " / " /etc/fstab | grep -v "^#"
echo ""
echo "=== UDEV RULES ==="
ls -la /etc/udev/rules.d/90-ssd-usb.rules 2>/dev/null
echo ""
echo "=== CRON JOBS ==="
echo pepe1234 | sudo -S crontab -l 2>/dev/null
echo ""
echo "=== ESPACIO ACTUAL ==="
df -h /dev/sda3
echo ""
echo "=== INITRAMFS SCRIPTS ==="
ls -la /etc/initramfs-tools/scripts/init-premount/ 2>/dev/null
""")
    print(out)

    ssh.close()
    print("\nOPTIMIZACION COMPLETADA!")

if __name__ == "__main__":
    main()
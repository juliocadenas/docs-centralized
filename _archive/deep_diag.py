#!/usr/bin/env python3
"""Diagnóstico profundo - SMART USB bridge + análisis de espacio."""
import paramiko
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=22, username=USER, password=PASS, timeout=20)

    cmd = """
echo '===== SMART con -d sat ====='
echo pepe1234 | sudo -S smartctl -d sat -a /dev/sda 2>&1
echo ''
echo '===== DETECCION USB ====='
lsusb 2>&1
echo ''
echo '===== UDEVADM ====='
echo pepe1234 | sudo -S udevadm info --query=all --name=/dev/sda 2>&1 | grep -iE 'ID_VENDOR|ID_MODEL|ID_BUS|ID_USB|ID_PATH'
echo ''
echo '===== SYS BLOCK ====='
echo pepe1234 | sudo -S cat /sys/block/sda/device/vendor 2>/dev/null
echo pepe1234 | sudo -S cat /sys/block/sda/device/model 2>/dev/null
echo ''
echo '===== ESPACIO EN / ====='
echo pepe1234 | sudo -S du -sh /var/* 2>/dev/null | sort -rh | head -10
echo ''
echo '--- /var/log ---'
echo pepe1234 | sudo -S du -sh /var/log/* 2>/dev/null | sort -rh | head -10
echo ''
echo '--- /home/pepe ---'
echo pepe1234 | sudo -S du -sh /home/pepe/* 2>/dev/null | sort -rh | head -15
echo ''
echo '--- /tmp ---'
echo pepe1234 | sudo -S du -sh /tmp/* 2>/dev/null | sort -rh | head -5
echo ''
echo '--- /root ---'
echo pepe1234 | sudo -S du -sh /root/* 2>/dev/null | sort -rh | head -5
echo ''
echo '--- /opt ---'
echo pepe1234 | sudo -S du -sh /opt/* 2>/dev/null | sort -rh | head -5
echo ''
echo '===== DOCKER ====='
echo pepe1234 | sudo -S docker system df 2>/dev/null || echo 'Docker no disponible'
echo ''
echo '===== JOURNAL SIZE ====='
echo pepe1234 | sudo -S journalctl --disk-usage 2>/dev/null
echo ''
echo '===== SNAP PACKAGES ====='
echo pepe1234 | sudo -S du -sh /snap/* 2>/dev/null | sort -rh | head -5
echo ''
echo '===== APT CACHE ====='
echo pepe1234 | sudo -S du -sh /var/cache/apt 2>/dev/null
echo ''
echo '===== FSCK CONFIG ACTUAL ====='
echo pepe1234 | sudo -S tune2fs -l /dev/sda3 2>/dev/null | grep -iE 'mount count|maximum|last|state|check'
echo ''
echo '===== FIN ====='
"""

    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)
    output = stdout.read().decode('utf-8', errors='replace')
    errors = stderr.read().decode('utf-8', errors='replace')

    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(script_dir, "RESULTADO_PROFUNDO.txt")
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write(output)
        if errors.strip():
            f.write("\n\n--- STDERR ---\n")
            f.write(errors[:2000])

    print(f"Guardado en: {result_path}")
    print(f"Tamano del output: {len(output)} chars")
    ssh.close()

if __name__ == "__main__":
    main()
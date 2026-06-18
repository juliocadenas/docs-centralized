#!/usr/bin/env python3
"""Diagnóstico remoto del disco del servidor Madrid NAB9."""
import paramiko
import os
import sys

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Conectando a {USER}@{HOST}...")
    ssh.connect(HOST, port=22, username=USER, password=PASS, timeout=20)
    print("CONECTADO!\n")

    # Comando de diagnóstico - todo en uno
    cmd = r"""
echo '===== 1. SISTEMA ====='
uname -a
uptime
echo ''
echo '===== 2. DISCOS DETECTADOS ====='
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL 2>/dev/null
echo ''
echo '===== 3. SALUD SMART ====='
if ! command -v smartctl &>/dev/null; then
    echo 'Instalando smartmontools...'
    echo pepe1234 | sudo -S apt install -y smartmontools 2>&1 | tail -3
fi
echo '--- Test general ---'
echo pepe1234 | sudo -S smartctl -H /dev/sda 2>/dev/null
echo ''
echo '--- Atributos criticos ---'
echo pepe1234 | sudo -S smartctl -A /dev/sda 2>/dev/null
echo ''
echo '===== 4. ERRORES EN DMESG ====='
echo pepe1234 | sudo -S dmesg 2>/dev/null | grep -iE 'error|ata|sata|ext4|i\/o' | tail -30
echo ''
echo '===== 5. FILESYSTEM /dev/sda3 ====='
echo pepe1234 | sudo -S dumpe2fs /dev/sda3 2>/dev/null | grep -iE 'state|mount count|maximum|last checked|lifetime|error'
echo ''
echo '===== 6. ESPACIO ====='
df -h
echo ''
echo '===== 7. RAM ====='
free -h
echo ''
echo '===== 8. UPS? ====='
if command -v upsc &>/dev/null; then echo 'UPS detectado'; else echo 'NO HAY UPS'; fi
echo ''
echo '===== FIN ====='
"""

    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)
    output = stdout.read().decode('utf-8', errors='replace')
    errors = stderr.read().decode('utf-8', errors='replace')

    print(output)
    if errors.strip():
        print("\n--- STDERR ---")
        print(errors)

    # Guardar con path absoluto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(script_dir, "RESULTADO_DIAGNOSTICO.txt")
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write(output)
        if errors.strip():
            f.write("\n\n--- STDERR ---\n")
            f.write(errors)

    print(f"\nResultado guardado en: {result_path}")
    ssh.close()

if __name__ == "__main__":
    main()
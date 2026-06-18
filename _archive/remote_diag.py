#!/usr/bin/env python3
"""
Diagnóstico remoto del servidor Madrid (NAB9) vía SSH.
Ejecuta el script de diagnóstico completo en el servidor y trae los resultados.
"""
import paramiko
import sys
import os

HOST = "100.105.27.27"
PORT = 22
USER = "julio"

# Obtener password de argumento o variable de entorno
PASSWORD = os.environ.get("SSH_PASS", "")
if len(sys.argv) > 1:
    PASSWORD = sys.argv[1]

if not PASSWORD:
    print("❌ ERROR: Necesito la contraseña SSH del servidor.")
    print("   Uso: python remote_diag.py <password_ssh>")
    print("   O:   set SSH_PASS=tu_password && python remote_diag.py")
    sys.exit(1)

def run_remote_commands():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"🔗 Conectando a {USER}@{HOST}:{PORT} ...")
    try:
        ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=20)
    except paramiko.AuthenticationException:
        print("❌ ERROR: Contraseña incorrecta")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR de conexión: {e}")
        sys.exit(1)

    print("✅ Conectado!\n")

    # Comandos de diagnóstico
    diag_script = r'''
echo "================================================"
echo "  DIAGNÓSTICO DE SALUD DEL DISCO - NAB9 Madrid"
echo "  Fecha: $(date)"
echo "================================================"
echo ""

echo ">>> 1. SISTEMA <<<"
uname -a
uptime
echo ""

echo ">>> 2. DISCOS DETECTADOS <<<"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL 2>/dev/null
echo ""

echo ">>> 3. SALUD SMART DEL DISCO <<<"
if command -v smartctl &>/dev/null; then
    echo "--- Test general ---"
    sudo smartctl -H /dev/sda 2>/dev/null || smartctl -H /dev/sda 2>/dev/null
    echo ""
    echo "--- Atributos críticos ---"
    sudo smartctl -A /dev/sda 2>/dev/null | grep -E "Reallocated|Current_Pending|Offline_Uncorrectable|UDMA_CRC|Power_On_Hours|Temperature|Endurance" || \
    smartctl -A /dev/sda 2>/dev/null | grep -E "Reallocated|Current_Pending|Offline_Uncorrectable|UDMA_CRC|Power_On_Hours|Temperature|Endurance"
    echo ""
    echo "--- Errores SMART ---"
    sudo smartctl -l error /dev/sda 2>/dev/null | tail -20 || smartctl -l error /dev/sda 2>/dev/null | tail -20
else
    echo "⚠️ smartmontools NO instalado - Instalar: sudo apt install smartmontools"
    sudo apt install -y smartmontools 2>/dev/null && echo "(Instalado automáticamente)" || echo "(No se pudo instalar)"
fi
echo ""

echo ">>> 4. ERRORES DE DISCO EN KERNEL <<<"
sudo dmesg | grep -i "error\|ata\|sata\|ext4\|i/o" | tail -30
echo ""

echo ">>> 5. ESTADO DEL FILESYSTEM /dev/sda3 <<<"
sudo dumpe2fs /dev/sda3 2>/dev/null | grep -E "Filesystem state|Mount count|Maximum mount|Last checked|Lifetime writes|Error"
echo ""

echo ">>> 6. ERRORES EXT4 EN JOURNAL <<<"
sudo journalctl -b -p err 2>/dev/null | grep -i "ext4\|disk\|ata\|sda\|i/o" | tail -20
echo ""

echo ">>> 7. HISTORIAL DE ARRANQUES <<<"
journalctl --list-boots 2>/dev/null | tail -10
echo ""

echo ">>> 8. ESPACIO EN DISCO <<<"
df -h
echo ""

echo ">>> 9. MEMORIA RAM <<<"
free -h
echo ""

echo ">>> 10. TEMPERATURA DISCO <<<"
sudo smartctl -A /dev/sda 2>/dev/null | grep -i temp || hddtemp /dev/sda 2>/dev/null || echo "N/A"
echo ""

echo ">>> 11. UPS DETECTADO? <<<"
if command -v upsc &>/dev/null; then
    echo "UPS detectado (nut-client instalado)"
else
    echo "❌ NO hay UPS detectado - El servidor NO tiene batería de respaldo"
fi
echo ""

echo "================================================"
echo "  FIN DEL DIAGNÓSTICO"
echo "================================================"
'''

    print("=" * 60)
    print("  EJECUTANDO DIAGNÓSTICO REMOTO...")
    print("=" * 60 + "\n")

    stdin, stdout, stderr = ssh.exec_command(diag_script, timeout=60)
    output = stdout.read().decode('utf-8', errors='replace')
    errors = stderr.read().decode('utf-8', errors='replace')

    print(output)
    if errors.strip():
        print("\n--- STDERR ---")
        print(errors)

    # Guardar resultado en archivo local
    result_file = os.path.join(os.path.dirname(__file__), "RESULTADO_DIAGNOSTICO.txt")
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(output)
        if errors.strip():
            f.write("\n\n--- STDERR ---\n")
            f.write(errors)

    print(f"\n📁 Resultado guardado en: {result_file}")

    ssh.close()
    print("🔌 Conexión cerrada.")

if __name__ == "__main__":
    run_remote_commands()
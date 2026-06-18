#!/bin/bash
# ============================================================================
# DIAGNÓSTICO COMPLETO DE SALUD DEL DISCO - Servidor Madrid NAB9
# Ejecutar como root: sudo bash diagnostico_disco.sh
# ============================================================================

echo "================================================"
echo "  DIAGNÓSTICO DE SALUD DEL DISCO - NAB9 Madrid"
echo "  Fecha: $(date)"
echo "================================================"
echo ""

# 1. INFORMACIÓN BÁSICA DEL DISCO
echo ">>> 1. DISCOS DETECTADOS <<<"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL 2>/dev/null
echo ""

# 2. SALUD SMART (LO MÁS IMPORTANTE)
echo ">>> 2. SALUD SMART DEL DISCO /dev/sda <<<"
if command -v smartctl &> /dev/null; then
    echo "--- Test general de salud ---"
    smartctl -H /dev/sda 2>/dev/null
    echo ""
    echo "--- Atributos críticos de desgaste ---"
    smartctl -A /dev/sda 2>/dev/null | grep -E "Reallocated_Sector|Current_Pending|Offline_Uncorrectable|UDMA_CRC|Power_On_Hours|Temperature|Endurance"
    echo ""
    echo "--- Errores SMART ---"
    smartctl -l error /dev/sda 2>/dev/null | tail -20
    echo ""
    echo "--- Tests autoejecutados ---"
    smartctl -l selftest /dev/sda 2>/dev/null | tail -15
else
    echo "⚠️ smartctl no está instalado. Instalar con: sudo apt install smartmontools"
fi
echo ""

# 3. ERRORES DE DISCO EN KERNEL
echo ">>> 3. ERRORES DE DISCO EN DMESG (últimos) <<<"
dmesg | grep -i "error\|ata\|sata\|ext4\|i/o" | tail -30
echo ""

# 4. ESTADO DEL FILESYSTEM
echo ">>> 4. ESTADO DEL FILESYSTEM /dev/sda3 <<<"
dumpe2fs /dev/sda3 2>/dev/null | grep -E "Filesystem state|Mount count|Maximum mount|Last checked|Lifetime writes|Filesystem features|Error"
echo ""

# 5. ERRORES EN LOGS DEL SISTEMA
echo ">>> 5. ERRORES EXT4 EN JOURNAL (último boot) <<<"
journalctl -b -p err 2>/dev/null | grep -i "ext4\|disk\|ata\|sda\|i/o" | tail -20
echo ""

# 6. HISTORIAL DE BOOTS (para detectar cortes de energía)
echo ">>> 6. HISTORIAL DE ARRANQUES (últimos 10) <<<"
journalctl --list-boots 2>/dev/null | tail -10
echo ""

# 7. ESPACIO EN DISCO
echo ">>> 7. ESPACIO EN DISCO <<<"
df -h
echo ""

# 8. MEMORIA RAM (para descartar RAM defectuosa)
echo ">>> 8. MEMORIA RAM <<<"
free -h
echo ""
echo "--- Errores de RAM (mcelog si disponible) ---"
if [ -f /var/log/mcelog ]; then
    tail -10 /var/log/mcelog
else
    echo "No hay mcelog configurado"
fi
echo ""

# 9. TEMPERATURA DEL DISCO
echo ">>> 9. TEMPERATURA DEL DISCO <<<"
if command -v hddtemp &> /dev/null; then
    hddtemp /dev/sda 2>/dev/null
elif command -v smartctl &> /dev/null; then
    smartctl -A /dev/sda 2>/dev/null | grep -i "temperature"
else
    echo "Instalar hddtemp: sudo apt install hddtemp"
fi
echo ""

# 10. UPS / ENERGENCIA
echo ">>> 10. DETECCIÓN DE UPS <<<"
if command -v upsc &> /dev/null; then
    upsc -l 2>/dev/null
    echo "(Si hay UPS listado, está conectado)"
else
    echo "No hay nut-ups instalado - NO se detecta UPS"
fi
echo ""

echo "================================================"
echo "  FIN DEL DIAGNÓSTICO"
echo "================================================"
echo ""
echo "PARA MANDAR RESULTADOS A JULIO:"
echo "sudo bash diagnostico_disco.sh > resultado_diagnostico.txt 2>&1"
echo "Y mandar el archivo resultado_diagnostico.txt"
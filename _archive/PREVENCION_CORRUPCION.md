# 🛡️ POR QUÉ PASA Y CÓMO PREVENIRLO

## ❓ POR QUÉ OCURRE TAN REPETIDAMENTE

**La corrupción recurrente de `/dev/sda3` NO es normal.** Si pasa cada cierto tiempo, casi siempre es una de estas 3 causas:

### 🔴 Causa 1: DISCO MURIÉNDOSE (90% de los casos) — MÁS PROBABLE
- El disco tiene **sectores defectuosos físicos** que van empeorando
- Cada vez que escribe en un sector roto → corrupción
- Va a **empeorar progresivamente** hasta que el disco muera del todo
- **Solución:** Reemplazar el disco cuanto antes

### 🟡 Causa 2: RAM DEFECTUOSA (5% de los casos)
- La memoria RAM tiene errores → corrompe datos al escribir al disco
- **Síntoma:** Corrupción en partes aleatorias, no siempre el mismo archivo
- **Test:** `memtest86` (se ejecuta desde un USB al arrancar)

### 🟡 Causa 3: CORTE DE ENERGÍA (5% de los casos)
- Si el servidor se apaga de golpe (se va la luz, alguien lo apaga)
- Y **NO tiene UPS** (batería de respaldo)
- El sistema no se desmonta limpiamente → corrupción
- **Solución:** Comprar un UPS (SAI) — cuesta 50-100€

---

## ✅ SÍ SE PUEDE AUTOMATIZAR FSCK

### Pero hay un problema importante:

```
┌─────────────────────────────────────────────────┐
│  Si el servidor cae a initramfs, NO puede       │
│  ejecutar scripts internos porque el sistema    │
│  operativo NUNCA llegó a arrancar.              │
│                                                  │
│  El initramfs YA intenta fsck automáticamente,  │
│  pero cuando hay demasiada corrupción falla     │
│  y te deja en busybox manualmente.              │
└─────────────────────────────────────────────────┘
```

### Lo que SÍ podemos hacer (3 niveles de prevención):

---

## NIVEL 1: Forzar fsck en CADA arranque (RECOMENDADO)

Una vez que el servidor arranque (después de repararlo manualmente), ejecutar:

```bash
# Forzar fsck en cada reinicio (mount count = 1)
sudo tune2fs -c 1 /dev/sda3

# Verificar que se aplicó
sudo tune2fs -l /dev/sda3 | grep "Mount count"
```

**Esto hace que Linux revise el disco SIEMPRE antes de montarlo.**
Si hay errores menores los repara automáticamente sin caer a busybox.

**Para desactivarlo después (si el disco está sano):**
```bash
sudo tune2fs -c 0 /dev/sda3
```

---

## NIVEL 2: Script de fsck automático al iniciar

Crear un servicio systemd que ejecute fsck en modo solo-lectura:

```bash
sudo nano /etc/systemd/system/auto-fsck.service
```

Pegar esto:

```ini
[Unit]
Description=Auto filesystem check and repair
DefaultDependencies=no
Before=local-fs.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/fsck -y /dev/sda3
TimeoutSec=300

[Install]
WantedBy=multi-user.target
```

Activar:
```bash
sudo systemctl enable auto-fsck.service
```

> ⚠️ **Nota:** Esto ayuda con corrupción menor, pero si el disco está muriendo físicamente, no va a evitar que caiga a busybox.

---

## NIVEL 3: Script de MONITOREO que avise ANTES de que caiga

Este es el más útil. Crea un script que monitoree el disco y mande un email/aviso:

```bash
sudo nano /usr/local/bin/check-disk-health.sh
```

```bash
#!/bin/bash
# Monitorear salud del disco y enviar alertas

LOG="/var/log/disk-health.log"
EMAIL="juliocadenas@gmail.com"

# 1. Verificar SMART del disco
SMART_STATUS=$(smartctl -H /dev/sda 2>/dev/null | grep "result" | awk '{print $NF}')

if [ "$SMART_STATUS" != "PASSED" ]; then
    echo "$(date): ⚠️ DISCO FALLANDO - SMART: $SMART_STATUS" >> $LOG
    echo "ALERTA: El disco /dev/sda está fallando SMART: $SMART_STATUS" | \
    mail -s "🚨 ALERTA DISCO SERVIDOR MADRID" $EMAIL
fi

# 2. Contar errores en dmesg
ERRORS=$(dmesg | grep -i "error\|i/o error\|ext4-fs error" | tail -5)
if [ -n "$ERRORS" ]; then
    echo "$(date): Errores de disco detectados:" >> $LOG
    echo "$ERRORS" >> $LOG
fi

# 3. Verificar filesystem errores en logs
FS_ERRORS=$(journalctl -b | grep -i "ext4.*error\|EXT4-fs error" | wc -l)
if [ "$FS_ERRORS" -gt 0 ]; then
    echo "$(date): ⚠️ $FS_ERRORS errores de filesystem en este arranque" >> $LOG
fi
```

```bash
sudo chmod +x /usr/local/bin/check-disk-health.sh
```

Crear tarea programada (cron) que ejecute cada hora:
```bash
sudo crontab -e
```
Añadir línea:
```
0 * * * * /usr/local/bin/check-disk-health.sh
```

---

## 🔧 PASOS CRÍTICOS DE DIAGNÓSTICO (Una vez recuperado el servidor)

### Ejecutar en este ORDEN para encontrar la causa raíz:

```bash
# 1. ¿El disco está muriendo? (LO MÁS IMPORTANTE)
sudo smartctl -a /dev/sda
# Buscar "Reallocated_Sector_Ct" - si es > 0, el disco está muriendo
# Buscar "Current_Pending_Sector" - si es > 0, sectores por fallar

# 2. ¿Hay errores recientes de disco?
sudo dmesg | grep -i "error\|ata\|sata\|ext4"

# 3. ¿La RAM está bien? (dejar corriendo 1 hora mínimo)
sudo apt install memtester
sudo memtester 1G 1

# 4. ¿Hay cortes de energía registrados?
journalctl --list-boots | head -20
# Si hay muchos boots seguidos = cortes de energía

# 5. Estado detallado del filesystem
sudo dumpe2fs /dev/sda3 | grep -i "mount count\|last checked\|error"
```

---

## 📊 DECISIÓN FINAL

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  Si smartctl dice FAILED o tiene sectores              │
│  reallocados →  🚨 COMPRAR DISCO NUEVO YA             │
│  Es cuestión de tiempo que muera del todo.             │
│                                                        │
│  Si smartctl dice PASSED pero sigue corrompiéndose     │
│  → 🧪 Probar RAM con memtest86                         │
│                                                        │
│  Si todo pasa y no hay UPS                             │
│  → 🔌 COMPRAR UPS (SAI) — 50-100€                     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 📋 CHECKLIST PARA LA PERSONA EN MADRID

- [ ] Recuperar el servidor con `fsck -y /dev/sda3` (ver GUIA_REPARACION_DISCO.md)
- [ ] Una vez arrancado, ejecutar `sudo smartctl -a /dev/sda` y mandar foto
- [ ] Aplicar Nivel 1: `sudo tune2fs -c 1 /dev/sda3`
- [ ] Instalar script de monitoreo (Nivel 3)
- [ ] Si SMART falla → comprar disco nuevo
- [ ] Considerar comprar UPS si no tienen uno

---

**Creado por:** Julio (desde Venezuela)
**Para:** Servidor Madrid NAB9
**Fecha:** Junio 2026
# 🛡️ GUÍA COMPLETA - Optimización SSD USB en Minisforum NAB9

> **Servidor:** NAB9 (100.105.27.27) - Madrid  
> **Hardware:** Minisforum NAB9 + RTX 5080 (via OCuLink DEG2)  
> **SO:** Pop!_OS 24.04 con systemd-boot  
> **SSD:** PNY 250GB SATA SSD conectado por USB (adaptador OWC PA023U3)

---

## 📐 ARQUITECTURA DEL NAB9 (Entendiendo el problema)

```
┌─────────────────────────────────────────────┐
│           MINISFORUM NAB9                    │
│                                              │
│  Slot M.2-Key ──► Adaptador OCuLink ──►    │
│                   Base DEG2 ──► RTX 5080    │
│                                              │
│  Slot M.2 (E-key) ──► Tarjeta WiFi          │
│                                              │
│  Puerto USB3/4 ──► Adaptador OWC ──►       │
│                    SSD PNY 250GB (SISTEMA)  │
│                                              │
│  Puerto USB3   ──► Seagate 1.8TB            │
└─────────────────────────────────────────────┘
```

**El problema:** El SSD del sistema va por USB porque el único slot M.2-Key está ocupado por el adaptador OCuLink para la GPU. Las micro-desconexiones USB corrompen el filesystem ext4.

---

## ✅ OPTIMIZACIONES APLICADAS (6 capas de protección)

### Capa 1: Kernel cmdline (systemd-boot)
```
usbcore.autosuspend=-1 usbcore.usbfs_memory_mb=0
```
**Archivo:** `/boot/efi/loader/entries/Pop_OS-current.conf`  
**Archivo:** `/etc/kernelstub/configuration`  
**Efecto:** Desactiva el autosuspend USB a nivel de kernel desde el boot

### Capa 2: Modprobe
```bash
# /etc/modprobe.d/usb-ssd-fix.conf
options usbcore autosuspend=-1
```
**Efecto:** Aplica autosuspend=-1 cuando se carga el módulo usbcore

### Capa 3: tmpfiles.d
```
# /etc/tmpfiles.d/usb-autosuspend.conf
w /sys/module/usbcore/parameters/autosuspend - - - - -1
w /sys/bus/usb/devices/*/power/control - - - - on
```
**Efecto:** Refuerza autosuspend=-1 en cada boot vía systemd

### Capa 4: udev rules
```
# /etc/udev/rules.d/90-ssd-usb.rules
ACTION=="add|change", SUBSYSTEM=="usb", ATTR{idVendor}=="7825", ATTR{idProduct}=="a2a4", ATTR{power/control}="on"
```
**Efecto:** Desactiva power management específicamente para el adaptador OWC del SSD

### Capa 5: ext4 journaling + commit=1
```
# /etc/fstab
UUID=... / ext4 noatime,commit=1,errors=remount-ro 0 1
```
**Efecto:** Sincroniza el journal cada 1 segundo (en vez de 5s default). `errors=remount-ro` protege el disco si hay errores.  
**Nota:** `data=journal` en fstab causa problemas con systemd/initramfs (monta RO). Se configuró via `tune2fs -o journal_data` en su lugar.

### Capa 6: fsck en cada boot
```
# tune2fs
Maximum mount count: 1
```
**Efecto:** Verifica el disco en CADA arranque

---

## 🔄 RECOVERY AUTOMÁTICO (Si cae a busybox)

### Script en initramfs
```
/etc/initramfs-tools/scripts/init-premount/usb-ssd-recovery
```
**Qué hace:**
1. Espera hasta 30 segundos a que el SSD USB aparezca
2. Si no aparece, resetea el controlador USB
3. Ejecuta `fsck -y /dev/sda3` automáticamente
4. Continúa el boot sin intervención manual

---

## 📊 MONITOREO Y BACKUP

### Monitoreo automático (cada hora)
```cron
0 * * * * /usr/local/bin/disk-monitor.sh
```
Verifica: SMART, espacio en disco, errores ext4, errores USB

### Backup automático (diario a las 4am)
```cron
0 4 * * * /usr/local/bin/system-backup.sh
```
Crea backup en `/mnt/seagate/system_backup/` con:
- Config del sistema (fstab, systemd, udev, docker)
- Lista de paquetes instalados
- Snapshot SMART

---

## ⚠️ ACCIÓN REQUERIDA: REBOOT

Los cambios de kernel cmdline y data=journal requieren un reinicio para aplicar. **Después del reboot, verificar:**

```bash
# Verificar que autosuspend está desactivado
cat /sys/module/usbcore/parameters/autosuspend
# Debe mostrar: -1

# Verificar que data=journal está activo
mount | grep " / "
# Debe mostrar: data=journal

# Verificar cmdline
cat /proc/cmdline
# Debe incluir: usbcore.autosuspend=-1
```

---

## 💡 RECOMENDACIONES A FUTURO (cuando el presupuesto lo permita)

### Opción A: Torre PC nueva (recomendado a largo plazo)
- Torre ATX con slots PCIe nativos para la RTX 5080
- SSD NVMe M.2 para el sistema (sin USB)
- Presupuesto estimado: 500-800€ (sin GPU)

### Opción B: Mejorar el NAB9 actual
- Comprar un **UPS básico** (50-100€) — evita corrupción por cortes de luz
- Considerar un **cable USB de mayor calidad** o adaptador USB-SATA más estable
- El Seagate 1.8TB podría usarse para snapshots del sistema

### Opción C: Migrar el sistema al Seagate
- Instalar Linux en una partición del Seagate USB
- Aunque también va por USB, es un disco mecánico más resiliente a desconexiones
- NO recomendado para performance, pero sí para estabilidad

---

## 🔧 MANTENIMIENTO REGULAR

### Semanalmente
```bash
# Limpiar Docker (sigue habiendo 75GB recuperables)
docker image prune -a -f
docker builder prune -a -f

# Verificar espacio
df -h /

# Revisar log de salud del disco
cat /var/log/disk-health.log
```

### Mensualmente
```bash
# Verificar SMART
sudo smartctl -d sat -a /dev/sda | grep -E "PASSED|FAILED|pending|reallocated"

# Limpiar logs viejos
sudo journalctl --vacuum-time=7d
```

---

## 📋 ESTADO ACTUAL (post-optimización)

| Métrica | Valor | Estado |
|---------|-------|--------|
| SMART SSD | PASSED | ✅ Sano |
| Espacio libre | 31GB (14%) | ✅ Mejorado |
| USB autosuspend (runtime) | -1 | ✅ Desactivado |
| USB autosuspend (boot) | -1 | ✅ ACTIVO post-reboot |
| Kernel cmdline | usbcore.autosuspend=-1 | ✅ ACTIVO post-reboot |
| ext4 journal_data | tune2fs journal_data | ✅ Aplicado al superblock |
| commit=1 | fstab | ✅ Activo |
| Root mount | rw | ✅ Read-write |
| udev rules | Instaladas | ✅ Activo |
| modprobe | Instalado | ✅ Activo |
| fsck cada boot | Activado | ✅ Configurado |
| Recovery initramfs | Instalado | ✅ Configurado |
| Monitoreo cron | Cada hora | ✅ Activo |
| Backup cron | Diario 4am | ✅ Activo |
| Docker | active (4 containers) | ✅ Funcionando |
| USB errores dmesg | 0 | ✅ Limpio |

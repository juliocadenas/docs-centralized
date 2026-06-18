# ☢️ PLAN NUCLEAR - Auto-Recuperación Server NAB9

> **Objetivo:** Que el servidor NUNCA MÁS se quede trabado en busybox initramfs requiriendo intervención física.
>
> **Fecha:** 18 junio 2026 | **Servidor:** NAB9 (Pop!_OS) - 100.105.27.27

---

## 📋 RESUMEN EJECUTIVO

El servidor ha caído a `busybox initramfs` múltiples veces. Cada vez requiere que alguien en Madrid conecte monitor+teclado físicamente. Esto es inaceptable para un servidor remoto.

### Causa raíz de la cadena de fallos:
```
VRAM OOM (16GB agotados) 
  → Driver NVIDIA crashea 
    → Kernel panic / estado inconsistente 
      → Filesystem se corrompe 
        → Boot siguiente: fsck falla 
          → initramfs cae a busybox esperando input manual
            → 🔴 SERVER DOWN hasta intervención física
```

### Por qué las soluciones anteriores NO funcionaron:
| Solución intentada | Por qué falló |
|---|---|
| `tune2fs -c 1` (fsck cada boot) | No ayuda si hay MUCHA corrupción - initramfs cae a busybox igual |
| `usbcore.autosuspend=-1` | No previene corrupción causada por kernel panics |
| Scripts systemd/cron de monitoreo | **NUNCA se ejecutan** - el SO no arranca, systemd nunca inicia |
| GPU Manager en el Gateway | Se muere junto con el gateway en un OOM (el perro que se muerde la cola) |

**El problema fundamental:** Una vez en initramfs, lo ÚNICO que corre es el initramfs mismo. Por defecto cae a busybox esperando input manual. Hay que modificar el initramfs directamente.

---

## 🚨 FASE 1: Recuperación Física (UNA última vez)

> ⚠️ **No hay forma de saltarse esto remotamente.** El servidor está abajo.

### Pasos para la persona en Madrid:

1. **Conectar monitor (HDMI/DP) + teclado USB al NAB9**
2. **Encender/reiniciar el servidor**
3. **Cuando aparezca `(initramfs)`:**
   ```bash
   # Ver qué partición es root (normalmente sda3)
   ls /dev/sd*
   
   # Ejecutar fsck con auto-reparación
   fsck -y /dev/sda3
   
   # Cuando termine, continuar el boot
   exit
   ```
4. **Si `exit` no funciona y vuelve a busybox:**
   ```bash
   fsck -y /dev/sda3
   reboot
   ```
5. **Una vez arrancado, avisar a Julio para aplicar Fases 2-6 remotamente**

### Verificación post-recovery:
```bash
ssh pepe@100.105.27.27
nvidia-smi
sudo systemctl is-active ai-hub-gateway ollama
```

---

## ☢️ FASE 2: Modificar el INITRAMFS (La Solución Real)

> **Esto es lo que NUNCA se hizo antes.** Modificar el initramfs para auto-repararse.

### 2.1 - Script de auto-fsck en el initramfs

Archivo: `/etc/initramfs-tools/scripts/init-premount/zz-auto-fsck`

Este script se ejecuta ANTES de montar root, dentro del initramfs:
- **Siempre** ejecuta `fsck -y` en la partición root
- Si fsck tiene errores fatales, reboot automático tras 10 segundos
- **NUNCA** cae a busybox shell

### 2.2 - Script anti-panic en el initramfs

Archivo: `/etc/initramfs-tools/scripts/init-bottom/zz-panic-guard`

Este script parchea el comportamiento de panic dentro del initramfs:
- Define `panic()` como una función que auto-rebootea
- Elimina la posibilidad de caer a shell interactivo

### 2.3 - Parámetros del kernel (kernelstub, NO grub)

Pop!_OS usa `kernelstub` + `systemd-boot`, NO grub. Los parámetros correctos:

```bash
# Parámetros a añadir al kernel cmdline:
panic=10                    # Auto-reboot 10s después de kernel panic
fsck.mode=force             # Forzar fsck SIEMPRE
fsck.repair=yes             # Auto-reparar todos los errores
boot.repair=yes             # Intentar reparar boot
```

### 2.4 - Reconstruir initramfs

```bash
sudo update-initramfs -u -k all
```

### Orden de ejecución:
1. Copiar scripts a `/etc/initramfs-tools/scripts/`
2. Hacer ejecutables (`chmod +x`)
3. Modificar kernelstub configuration + EFI cmdline
4. `sudo update-initramfs -u -k all`
5. Verificar con `lsinitramfs` que los scripts están incluidos

---

## 🛡️ FASE 3: Watchdog VRAM a nivel OS (Prevenir OOM)

> El GPU Manager actual vive dentro del Gateway. Si el Gateway muere por OOM, el manager muere también. Necesitamos un watchdog **independiente** a nivel sistema operativo.

### 3.1 - Servicio systemd: `vram-watchdog.service`

Script: `/usr/local/bin/vram-watchdog.sh`
- Corre cada 10 segundos
- Ejecuta `nvidia-smi` directamente (no depende de Python/Gateway)
- Si VRAM > 90% (14.4GB de 16GB): mata procesos GPU no-esenciales
- Si VRAM > 95% (15.2GB): mata TODOS los procesos GPU excepto Ollama
- Lleva log a `/var/log/vram-watchdog.log`

### 3.2 - Protección contra OOM Killer para servicios críticos

```bash
# El OOM killer nunca debe matar estos servicios:
sudo systemctl edit ollama
# Añadir:
# [Service]
# OOMScoreAdjust=-1000

sudo systemctl edit ai-hub-gateway
# [Service]
# OOMScoreAdjust=-500
# MemoryMax=4G
```

### 3.3 - Desactivar auto-start de servicios pesados

Todos los servicios GPU pesados deben tener `WantedBy=` vacío o enmascarados:
```bash
sudo systemctl disable comfyui wan2gp documusic musetalk latentsync liveportrait hallo2
```

---

## 🔧 FASE 4: Hardening del Filesystem

### 4.1 - Forzar fsck en cada boot
```bash
sudo tune2fs -c 1 /dev/sda3
```

### 4.2 - Data journaling (si no está activo)
Añadir `data=journal` al kernel cmdline para máxima integridad:
```
root=UUID=xxx ro data=journal panic=10 fsck.mode=force
```

### 4.3 - Sysrq safety
```bash
# /etc/sysctl.d/99-panic-reboot.conf
kernel.panic = 10           # Reboot tras 10s de panic
kernel.panic_on_oops = 1    # Panic on oops (en lugar de continuar inestable)
kernel.panic_on_oops_value = 1
kernel.sysrq = 1            # Habilitar SysRq para recovery manual remoto
```

---

## 📊 FASE 5: Monitoreo y Alertas Tempranas

### 5.1 - Health check cada 5 min (ya existe, mejorar)
```bash
# /usr/local/bin/health-check.sh
# - Verificar filesystem errors en dmesg
# - Verificar SMART del disco
# - Si detecta problemas, forzar reboot limpio ANTES de que corrompa
```

### 5.2 - Watchdog de hardware (si la placa lo soporta)
```bash
sudo modprobe softdog
echo 1 | sudo tee /sys/class/leds/input5::scrolllock/brightness 2>/dev/null
# Configurar watchdog timer de 60s
```

---

## 📝 FASE 6: Documentación y Runbook

### Checklist post-deployment:
- [ ] Initramfs reconstruido y verificado
- [ ] Scripts de auto-fsck en initramfs
- [ ] kernelstub config actualizada
- [ ] VRAM watchdog service activo
- [ ] Servicios pesados deshabilitados de auto-start
- [ ] tune2fs -c 1 aplicado
- [ ] sysctl panic=10 aplicado
- [ ] SMART del disco verificado (excluir hardware defectuoso)
- [ ] Test: forzar panic y verificar auto-reboot

### Test de validación (post-deployment):
```bash
# Test 1: Verificar que el initramfs incluye los scripts
lsinitramfs /boot/initrd.img-$(uname -r) | grep -E "auto-fsck|panic-guard"

# Test 2: Verificar kernel cmdline
cat /proc/cmdline | grep -E "panic|fsck"

# Test 3: Verificar watchdog
systemctl status vram-watchdog

# Test 4: Simular VRAM alta (DANGER - solo en mantenimiento)
# python3 -c "import torch; x=torch.zeros(1, device='cuda')" &
# ...fill VRAM... watchdog debe matar procesos
```

---

## 🚀 DESPLIEGUE

Todo se despliega con un solo script:
```bash
python _deploy_nuclear_recovery.py
```

Este script hace todo vía SSH desde el PC de Julio. Solo necesita que el servidor esté arrancado (después de Fase 1).

---

## 📂 Archivos del Plan

| Archivo | Propósito |
|---------|-----------|
| `NUCLEAR_RECOVERY_PLAN.md` | Este documento (master) |
| `scripts/initramfs-auto-fsck.sh` | Script auto-fsck para initramfs |
| `scripts/initramfs-panic-guard.sh` | Script anti-panic para initramfs |
| `scripts/vram-watchdog.sh` | Watchdog VRAM nivel OS |
| `scripts/vram-watchdog.service` | Servicio systemd para watchdog |
| `_deploy_nuclear_recovery.py` | Script de despliegue via SSH |

---

**Creado por:** Julio (desde Venezuela)
**Para:** Servidor Madrid NAB9
**Fecha:** 18 junio 2026
**Versión:** 1.0 - PLAN NUCLEAR
# 🚨 Guía de Recuperación - Server NAB9 (busybox initramfs)

## Problema
El servidor se queda trabado en `busybox initramfs` después de ciertos reinicios.

## Causa Raíz Identificada
1. **VRAM OOM**: Todos los servicios AI cargaban modelos en GPU simultáneamente (16GB RTX 5080)
2. **GPU Driver Crash**: Cuando la VRAM se agota, el driver de NVIDIA se cuelga
3. **Kernel Panic/OOM**: Esto puede corromper el estado del filesystem
4. **initramfs stuck**: En el siguiente boot, fsck detecta errores y se queda esperando input en busybox

## Lo Que Ya Se Arregló (antes del crash)
- ✅ Todos los servicios pesados desactivados de auto-start
- ✅ Solo ollama + gateway arrancan al boot
- ✅ MuseTalk xtcocotools arreglado (numpy 1.26.4)
- ✅ gpu_manager.py mejorado (health checks HTTP + systemd)
- ✅ Watchdog de VRAM con auto-unload tras 10 min idle

## Pasos de Recuperación Física

### 1. Conectar monitor + teclado al NAB9

### 2. Solución A: fsck manual
```bash
(initramfs) fsck -y /dev/sda3
(initramfs) exit
```

### 3. Solución B: Si el disco USB se desconectó
```bash
(initramfs) ls /dev/sd*
(initramfs) exit
```

### 4. Después de boot exitoso
```bash
ssh pepe@100.105.27.27
sudo systemctl is-active comfyui documusic wan2gp musetalk latentsync liveportrait hallo2
# Todos deben decir "inactive"
nvidia-smi
```

## ☢️ PLAN NUCLEAR (Solución Definitiva)

> **NUEVO 18/06/2026:** Ver `NUCLEAR_RECOVERY_PLAN.md` para la solución completa de 6 fases.

La prevención anterior no funcionaba porque los scripts systemd/cron NUNCA se ejecutan si el initramfs cae a busybox. La solución real es **modificar el initramfs mismo** para auto-repararse.

### Despliegue (después de recuperación física):
```bash
# Desplegar las 6 fases vía SSH:
python _deploy_nuclear_recovery.py

# O solo una fase específica:
python _deploy_nuclear_recovery.py --phase 2  # Solo initramfs
python _deploy_nuclear_recovery.py --phase 3  # Solo VRAM watchdog

# Dry run (ver qué haría sin aplicar cambios):
python _deploy_nuclear_recovery.py --dry-run
```

### Lo que hace el Plan Nuclear:
1. **Initramfs auto-fsck** - Auto-repara el disco ANTES de montar root
2. **Panic guard** - Si algo falla, auto-reboot en lugar de caer a busybox
3. **VRAM watchdog OS-level** - Previene OOM independientemente del Gateway
4. **Filesystem hardening** - `tune2fs -c 1`, `data=journal`, sysctl panic=10
5. **Health checks mejorados** - Detección temprana de problemas
6. **Verificación automática** - Chequea que todo quedó bien instalado

### NOTA IMPORTANTE sobre Pop!_OS:
Pop!_OS usa `systemd-boot` + `kernelstub`, **NO GRUB**.
Los parámetros del kernel se cambian con `kernelstub`, no con `update-grub`.

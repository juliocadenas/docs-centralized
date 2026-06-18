# 🚨 Guía de Recuperación - Server NAB9 (busybox initramfs)

> **Última actualización:** 18/06/2026 - Sistema recuperado y protegido con 6 capas anti-crash

## Estado Actual: ✅ OPERATIVO

```
Gateway:    OK (http://100.105.27.27:9000/v1)
VRAM:       ~700-1000MB / 16.3GB (4-6%)
LLM:        llama3.1:latest respondiendo
TTS:        Piper (es_ES-sharvard) verificado
STT:        Whisper medium (lazy-load) verificado
```

## Problema Original
El servidor se quedaba trabado en `busybox initramfs` después de crash por VRAM OOM:
1. **VRAM OOM** - Todos los modelos cargados a la vez en 16GB RTX 5080
2. **GPU Driver Crash** - NVIDIA driver se cuelga al agotarse VRAM
3. **Kernel Panic/OOM** - Corrompe filesystem
4. **initramfs stuck** - En boot, fsck detecta errores y cae a busybox

## ✅ Solución Aplicada - 6 Capas de Protección

### Capa 1: Initramfs Auto-Fsck (Script)
- **Script:** `scripts/initramfs-auto-fsck.sh`
- Auto-ejecuta `fsck -y` SIEMPRE (sin preguntar)
- NUNCA cae a busybox shell - si fsck falla, reboot automático

### Capa 2: Panic Guard
- **Script:** `scripts/initramfs-panic-guard.sh`
- **Config:** `scripts/99-panic-reboot.conf`
- Patchea `panic()` del initramfs para auto-recuperar
- `kernel.panic=10` (auto-reboot tras 10s)

### Capa 3: VRAM Watchdog (OS-level)
- **Script:** `scripts/vram-watchdog.sh`
- **Service:** `scripts/vram-watchdog.service`
- Monitorea VRAM cada 30s, mata procesos antes de OOM
- Funciona independientemente del Gateway

### Capa 4: Lazy-Loading Architecture
- Solo Ollama es `always_on` (carga al boot)
- TTS, STT, Avatars, Effects = lazy-load (cargan bajo demanda)
- Auto-unload después de 5 min idle
- Whisper cambió de large-v3 (9.6GB) a medium (0MB idle)

### Capa 5: Systemd OOM Drop-ins
- **Config:** `scripts/oom-protection-dropins.conf`
- Memory limits per service
- Restart policies con backoff

### Capa 6: Gateway Health Checks
- `always_on=False` para todos excepto Ollama
- Status reporta "OK" correctamente
- Health checks HTTP + systemd

## Pasos de Recuperación Física (Si pasa de nuevo)

> **IMPORTANTE:** Con las 6 capas instaladas, esto NO debería ser necesario.
> Pero si ocurre corrupción severa del filesystem:

### 1. Conectar monitor + teclado al NAB9

### 2. fsck manual
```bash
(initramfs) fsck -y /dev/sda3
(initramfs) exit
```

### 3. Después de boot exitoso
```bash
ssh pepe@100.105.27.27
# Verificar servicios
python scripts/check_system.py
# Si algo está caído:
sudo systemctl restart ai-hub-gateway ollama tts stt comfyui
```

## Monitoreo Rutinario

### Quick check (desde cualquier PC):
```bash
python scripts/check_system.py
```

### API endpoints útiles:
```bash
# Estado del sistema
curl http://100.105.27.27:9000/v1/status | python -m json.tool

# Infraestructura completa
curl http://100.105.27.27:9000/v1/infrastructure | python -m json.tool

# Modelos disponibles
curl http://100.105.27.27:9000/v1/models | python -m json.tool

# Docs
# http://100.105.27.27:9000/docs
```

### Iniciar un servicio manualmente:
```bash
curl -X POST http://100.105.27.27:9000/v1/services/musetalk/start
curl -X POST http://100.105.27.27:9000/v1/services/rembg/start
```

## NOTA sobre Pop!_OS
Pop!_OS usa `systemd-boot` + `kernelstub`, **NO GRUB**.
Los parámetros del kernel se cambian con `kernelstub`, no con `update-grub`.
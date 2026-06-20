# 🗺️ AI Hub Madrid - Mapa de Infraestructura (Source of Truth)

> **⚠️ Este es el archivo maestro.** Cualquier agente de IA (Cline, Cursor, etc.) debe leer este archivo para entender la infraestructura completa. Se actualiza con cada cambio en la infraestructura.
> 
> **Última actualización:** 19 junio 2026 (v3.2 - Qwen2.5 instalado + sincronizacion con estado real del gateway)

---

## 📋 Resumen Ejecutivo

Este documento describe la infraestructura de IA centralizada del ecosistema de Julio Cadenas. Todos los modelos de IA, APIs y servicios están centralizados en servidores propios (zero tokens). El **AI Hub Gateway** (:9000) es el punto de entrada unificado compatible con la API de OpenAI. El **AI Hub Studio** (:3000) es el portal web Netflix-style con todas las herramientas.

---

## 🌐 Topología de Red

```
Internet
    │
    ├── Tailscale Mesh VPN
    │
    ├── PC Julio (Windows 11) ─── Tailscale: (cuenta juliocadenas@gmail.com)
    │   └── Desarrollo local, Cline, Cursor, MCP Clients
    │
    ├── 🖥️ IA SERVER "Madrid" (NAB9 - Pop!_OS) ─── Tailscale: 100.105.27.27
    │   ├── IP LAN: 192.168.1.42
    │   ├── Hardware: RTX 5080 16GB VRAM + 32GB RAM
    │   ├── Disco SSD 220GB (sistema + Docker)
    │   ├── Disco USB 1.8TB Seagate → /mnt/seagate (AI Hub)
    │   │
    │   ├── 🧠 AI Hub Gateway ── :9000  (API unificada)
    │   ├── 🗣️ Ollama ────────── :11434 (LLM local)
    │   ├── 🖼️ ComfyUI ───────── :8188  (Imagen/Video)
    │   ├── 🎬 Wan2GP ────────── :7860  (Video optimizado GPU)
    │   ├── 🎵 DocuMusic ─────── :8000  (Audio/Musica)
    │   ├── 🌐 AI Hub Studio ─── :3000  (Portal web Docker)
    │   ├── 🎭 Hallo2 ────────── :8070  (Avatar hablando)
    │   ├── 👄 LatentSync ────── :8043  (Lip-sync perfecto)
    │   ├── 🖼️ LivePortrait ──── :8044  (Animacion facial)
    │   ├── 🗣️ MuseTalk ──────── :8040  (Lip-sync tiempo real)
    │   ├── 🗣️ Piper TTS ─────── :8010  (Text-to-Speech)
    │   ├── 🎤 Whisper STT ───── :8020  (Speech-to-Text)
    │   ├── ✂️ Rembg ─────────── :8050  (Quitar fondo)
    │   ├── 🔍 Real-ESRGAN ───── :8051  (Upscaler 4x)
    │   ├── ⚡ Higgsfield AI ──── :8052  (Efectos video)
    │   ├── 🎥 CogVideoX ─────── :7861  (Video generation HQ)
    │   ├── 📖 StoryDiffusion ── :7862  (Comic → Video)
    │   └── (futuros modelos...)
    │
    └── 🏢 SERVIDOR01 (Proxmox) ─── Tailscale: 100.83.253.87
        ├── IP LAN: 192.168.1.210
        ├── Hardware: Xeon 48 nucleos, 188GB RAM, 2.45TB LVM
        ├── Europa Scraper ──── :8001
        └── NFS Exports → /mnt/ai_models, /srv/comfyui_models
```

---

## 🔌 Servicios y Puertos

### IA SERVER (Madrid) - 100.105.27.27 / 192.168.1.42

| Puerto | Servicio | Tipo | Estado | Descripcion |
|--------|----------|------|--------|-------------|
| **9000** | **AI Hub Gateway** | systemd | ✅ Operativo | API unificada compatible OpenAI |
| **3000** | **AI Hub Studio** | Docker | ✅ Operativo | Portal web Netflix-style con todas las herramientas |
| 7860 | Wan2GP | Nativo (systemd) | ✅ Operativo | Video generation (WAN 2.1, LTX, Hunyuan) |
| 8000 | DocuMusic Backend | Docker | ✅ Operativo | Audio generation (YuE, ACE-Step, DiffRhythm) |
| 8188 | ComfyUI | Nativo (systemd) | ✅ Operativo | Image/Video generation (nodes-based) |
| 11434 | Ollama | Nativo | ✅ Operativo | LLM (llama3.1, futuros modelos) |
| 8070 | Hallo2 | Python (serve_avatars) | ✅ Operativo | Avatar hablando (Foto+Audio→Video) - HeyGen |
| 8043 | LatentSync | Python (serve_avatars) | ✅ Operativo | Lip-sync perfecto (ByteDance) - HeyGen Lip-sync |
| 8044 | LivePortrait | Python (serve_avatars) | ✅ Operativo | Animacion facial (KwaiVGI) - HeyGen Express |
| 8040 | MuseTalk | Python (serve_avatars) | ✅ Operativo | Lip-sync tiempo real (TME) - HeyGen Live |
| 8010 | Piper TTS | Python (systemd) | ✅ Operativo | Text-to-Speech (Piper 1.4.2, CPU) |
| 8020 | Whisper STT | Python (systemd) | ✅ Operativo | Speech-to-Text (Whisper large-v3, GPU) |
| 8050 | Rembg | Python (effects_svc) | ✅ Operativo | Quitar fondo - Remove.bg |
| 8051 | Real-ESRGAN | Python (effects_svc) | ✅ Operativo | Upscaler 4x - Upscale.media |
| 8052 | Higgsfield AI | Python (effects_svc) | ✅ Operativo | Efectos de video - Higgsfield AI |
| 7861 | CogVideoX | Python (HTTP server) | 🟡 Instalando | Video generation HQ (THUDM) - Pika AI |
| 7862 | StoryDiffusion | Python (HTTP server) | 🟡 Instalando | Character→Comic→Video - Series YouTube |
| 5173 | DocuMusic Frontend | Local | ✅ Operativo | React dev server (solo desarrollo) |

### Servicios Planificados (IA SERVER)

| Puerto | Servicio | Categoria | VRAM | Prioridad |
|--------|----------|-----------|------|-----------|
| 7863 | Open-Sora | Video generation tipo Sora | ~10GB | ⭐ Alta |
| 8081 | AI-VTuber | VTuber Pipeline | ~4GB | Media |
| 8082 | Digital Human | Full Avatar Pipeline | ~8GB | Media |
| 8030 | Meta SAM2 | Segmentacion | ~4GB | Media |
| 8041 | SadTalker | Lip-sync alternativo | ~4GB | Media |
| 8042 | Wav2Lip | Lip-sync ligero | ~2GB | Media |
| 8050 | InsightFace | Reconocimiento facial | ~2GB | Media |
| 8061 | DWpose | Pose Detection | ~2GB | Media |
| 8060 | YOLOv8 | Deteccion objetos | ~2GB | Baja |

### SERVIDOR01 (Proxmox) - 100.83.253.87 / 192.168.1.210

| Puerto | Servicio | Descripcion |
|--------|----------|-------------|
| 8001 | Europa Scraper | FastAPI scraper + AI search |

---

## 💾 Almacenamiento Centralizado

### Disco Seagate 1.8TB (`/mnt/seagate/`) - AI Hub

```
/mnt/seagate/
├── models/                          # ✦ ALMACEN CANONICO
│   ├── audio/                       # 56GB - Modelos de audio
│   │   ├── music_generation/        # YuE, ACE-Step, HeartMuLa, DiffRhythm2
│   │   ├── codecs/                  # XCodec, MuQ
│   │   └── language/                # XLM-RoBERTa
│   ├── vision/                      # 49GB - Modelos de video/imagen
│   │   ├── checkpoints/             # WAN 2.1, LTX Video, HunyuanVideo, SD v1.5
│   │   ├── text_encoders/           # T5 XXL FP8
│   │   ├── clip/                    # CLIP L, CLIP Vision G
│   │   ├── vae/                     # Hunyuan VAE
│   │   ├── controlnet/              # ControlNet models
│   │   ├── ip_adapter/              # IP-Adapter models
│   │   ├── loras/                   # LoRAs
│   │   └── upscale_models/          # ESRGAN
│   ├── hallo2/                      # 13GB - Hallo2 checkpoints (Fudan)
│   ├── latentsync/                  # 7.5GB - LatentSync checkpoints (ByteDance)
│   ├── liveportrait/                # 2GB - LivePortrait checkpoints (KwaiVGI)
│   ├── musetalk/                    # 6.4GB - MuseTalk checkpoints (TME)
│   └── llm/                         # Modelos de lenguaje (Ollama)
├── hallo2/                          # Repo Hallo2 (Fudan)
├── LatentSync/                      # Repo LatentSync (ByteDance)
├── LivePortrait/                    # Repo LivePortrait (KwaiVGI)
├── MuseTalk/                        # Repo MuseTalk (TME)
├── links/                           # ✦ SYMLINKS DE COMPATIBILIDAD
│   ├── comfyui/                     # → ComfyUI extra_model_paths.yaml
│   └── huggingface/                 # → HuggingFace cache compatibility
├── api/                             # APIs y registry
│   └── model_registry.yaml          # Catalogo central
├── ai-hub-gateway/                  # 🧠 Gateway API
├── ai-hub-studio/                   # 🌐 Portal web (Docker build)
├── local_backup/                    # Source code repos
├── output/                          # Output de ComfyUI
├── input/                           # Input de ComfyUI
├── cache/                           # Cache comun
└── backup/                          # Backups locales
```

### Symlinks clave
- `~/AI_MODELS` → `/mnt/seagate` (backward compatibility)
- `/mnt/seagate/links/comfyui/*` → `../../models/vision/*` (14 symlinks)

---

## 🧠 AI Hub Gateway API

### Endpoint Base
```
http://100.105.27.27:9000/v1
```

### Endpoints Disponibles

| Metodo | Endpoint | Descripcion | Servicio Backend |
|--------|----------|-------------|-----------------|
| GET | `/v1/models` | Lista todos los modelos disponibles | Registry |
| GET | `/v1/status` | Status de servicios + VRAM usage | GPU Manager |
| GET | `/v1/infrastructure` | Este mapa en formato JSON (tiempo real) | Gateway |
| POST | `/v1/chat/completions` | Chat con LLM (formato OpenAI) | Ollama |
| POST | `/v1/images/generations` | Generar imagenes | ComfyUI |
| POST | `/v1/audio/generations` | Generar audio/musica | DocuMusic |
| POST | `/v1/video/generations` | Generar video | Wan2GP |
| POST | `/v1/audio/speech` | Text-to-Speech (Piper) | Piper TTS :8010 |
| POST | `/v1/audio/transcriptions` | Speech-to-Text (Whisper) | Whisper STT :8020 |
| POST | `/v1/services/{name}/start` | Iniciar servicio bajo demanda | GPU Manager |
| POST | `/v1/services/{name}/stop` | Detener servicio (liberar VRAM) | GPU Manager |

### Ejemplo de uso (compatible OpenAI)
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://100.105.27.27:9000/v1",
    api_key="local"  # No se necesita API key real
)

response = client.chat.completions.create(
    model="llama3.1",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Ejemplo de uso (curl)
```bash
# Chat
curl http://100.105.27.27:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.1","messages":[{"role":"user","content":"Hello"}]}'

# Generar imagen
curl http://100.105.27.27:9000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{"model":"sdxl","prompt":"a beautiful sunset"}'

# Ver modelos disponibles
curl http://100.105.27.27:9000/v1/models

# Status de infraestructura
curl http://100.105.27.27:9000/v1/status
```

---

## 📦 Catalogo de Modelos

### LLM (Ollama)
| Modelo | Tipo | VRAM | Endpoint |
|--------|------|------|----------|
| llama3.1 | Chat/Instruct | ~5GB | Gateway → Ollama :11434 |
| qwen2.5 | Chat/Multilingue | ~5GB | Gateway → Ollama :11434 |
| qwen2.5-coder | Programacion/Code | ~5GB | Gateway → Ollama :11434 |

### Audio (DocuMusic)
| Modelo | Tipo | VRAM | Endpoint |
|--------|------|------|----------|
| YuE (s1+s2) | Text-to-Music | ~8GB | Gateway → DocuMusic :8000 |
| ACE-Step v1 3.5B | Text-to-Music | ~4GB | Gateway → DocuMusic :8000 |
| DiffRhythm v2 | Text-to-Music | ~4GB | Gateway → DocuMusic :8000 |

### Vision - Video (Wan2GP / ComfyUI)
| Modelo | Tipo | VRAM | Endpoint |
|--------|------|------|----------|
| WAN 2.1 T2V 1.3B | Text-to-Video | ~6GB | Gateway → Wan2GP :7860 |
| LTX Video v0.9.8 | Text-to-Video | ~6GB | Gateway → Wan2GP :7860 |
| HunyuanVideo T2V | Text-to-Video | ~12GB | Gateway → ComfyUI :8188 |
| SD v1.5 | Text-to-Image | ~2GB | Gateway → ComfyUI :8188 |

### Avatares & Lip-sync (NUEVO - 8 junio 2026)
| Modelo | Tipo | VRAM | Puerto | Estado |
|--------|------|------|--------|--------|
| Hallo2 (Fudan) | Foto+Audio→Video | ~6GB | 8070 | ✅ Operativo |
| LatentSync (ByteDance) | Lip-sync perfecto | ~4GB | 8043 | ✅ Operativo |
| LivePortrait (KwaiVGI) | Animacion facial | ~4GB | 8044 | ✅ Operativo |
| MuseTalk (TME) | Lip-sync tiempo real | ~4GB | 8040 | ✅ Operativo |

### Voice - TTS & STT (NUEVO - 15 junio 2026)
| Modelo | Tipo | VRAM | Puerto | Estado |
|--------|------|------|--------|--------|
| Piper TTS 1.4.2 | Text-to-Speech | ~1GB (CPU) | 8010 | ✅ Operativo |
| Whisper large-v3 | Speech-to-Text | ~3GB (GPU) | 8020 | ✅ Operativo |

### Efectos & Edicion (NUEVO - 8 junio 2026)
| Modelo | Tipo | VRAM | Puerto | Estado |
|--------|------|------|--------|--------|
| Rembg | Quitar fondo | ~1GB | 8050 | ✅ Operativo |
| Real-ESRGAN | Upscale 4x | ~4GB | 8051 | ✅ Operativo |
| Higgsfield AI | Efectos video | ~4GB | 8052 | ✅ Operativo |

### Video Generation Avanzada (NUEVO - 8 junio 2026)
| Modelo | Tipo | VRAM | Puerto | Estado |
|--------|------|------|--------|--------|
| CogVideoX (THUDM) | Video HQ | ~12GB | 7861 | 🟡 Instalando |
| StoryDiffusion | Comic→Video | ~6GB | 7862 | 🟡 Instalando |

---

## 🖥️ Gestion de VRAM (RTX 5080 - 16GB)

### Perfiles de ejecucion

**Perfil: Desarrollo (default)**
- Ollama: ~4GB ✅ siempre activo
- ComfyUI: variable ✅ siempre activo (se libera entre tasks)
- Total: ~6-8GB base

**Perfil: Video Pesado**
- Wan2GP: ~8-12GB
- Ollama: ~4GB
- Total: ~12-16GB (ComfyUI OFF)

**Perfil: Audio/Musica**
- DocuMusic: ~4-8GB (dentro de Docker)
- Ollama: ~4GB
- Total: ~8-12GB

**Perfil: Avatar/Lip-sync**
- Hallo2 + LatentSync: ~10GB
- Ollama: ~4GB
- Total: ~14-16GB (resto OFF)

**Perfil: Video HQ (CogVideoX/Open-Sora)**
- CogVideoX: ~12GB
- Ollama: ~4GB
- Total: ~16GB (full, resto OFF)

**Perfil: VTuber**
- TTS + Live2D + Ollama: ~8-10GB
- Total: ~8-10GB

### GPU Manager (en el Gateway)
El Gateway gestiona la VRAM inteligentemente con **auto-unload watchdog**:

**Watchdog (nuevo 17 junio 2026):**
- Cada 60s revisa servicios GPU idle
- Servicios sin actividad por >10 min se detienen automaticamente
- Libera VRAM para el siguiente servicio que la necesite
- Cada request reinicia el timer del servicio correspondiente

**Servicios always_on (siempre activos):**
- Ollama (LLM) - 4GB | Piper TTS - 0GB (CPU) | Whisper STT - 2GB | Rembg - 0.5GB

**Servicios on-demand (auto-unload):**
- ComfyUI, Wan2GP, DocuMusic, avatares, upscale
- Se inician al recibir request, se apagan tras 10 min idle

**Proteccion OOM (NUCLEAR RECOVERY - 18 junio 2026):**
- VRAM Watchdog systemd (vram-watchdog.service): monitorea cada 10s, mata procesos GPU si VRAM >90%%
- Systemd MemoryMax=4G en gateway
- Health check cron cada 5 min con auto-recovery
- Tailscale keepalive cron cada 5 min
- Kernel panic guard: kernel.panic=10 (auto-reboot tras 10s)
- Kernel OOM killer habilitado (vm.oom_kill_allocating_task=1)
- Initramfs auto-fsck: fsck -y automatico en boot (no busybox)
- Initramfs panic guard: auto-reboot si fsck falla (no espera input manual)

**Scripts de proteccion (en /mnt/seagate/scripts/):**
- health_check.sh - Health check cada 5 min
- backup.sh - Backup semanal
- vram-watchdog.sh - Monitor VRAM cada 10s

**Recovery scripts (en repo IA-HUB-MADRID1/scripts/):**
- initramfs-auto-fsck.sh - Auto-fsck en initramfs
- initramfs-panic-guard.sh - No busybox, auto-reboot
- 99-panic-reboot.conf - kernel.panic=10
- oom-protection-dropins.conf - Systemd OOM drop-ins
- vram-watchdog.service - Systemd VRAM watchdog

**Prioridad:** Ollama (siempre) > servicio solicitado > resto

**Telegram Alert Bot (NUEVO - 18 junio 2026):**
- Monitorea el sistema cada 2 min
- Alerta si Gateway cae, VRAM >85%, o servicios críticos offline
- Notifica cuando el servidor se reinicia
- Script: `scripts/telegram_alert_bot.py`
- Setup: ver `scripts/TELEGRAM_BOT_SETUP.md`
- Requiere: `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` (via @BotFather)

---

## 🔐 Credenciales y Acceso

### Servidor Madrid (NAB9)
- **SSH:** `ssh pepe@100.105.27.27` o `ssh pepe@192.168.1.42`
- **Password:** `pepe1234`
- **Tailscale:** cuenta `juliocadenas@gmail.com` ✅ (migrado 7 junio 2026)

### SERVIDOR01 (Proxmox)
- **SSH:** `ssh julio@100.83.253.87` o `ssh julio@192.168.1.210`
- **Password:** `julio@julio`
- **Tailscale:** cuenta `juliocadenas@gmail.com`

### API Key del Gateway
- **API Key:** `local` (sin autenticacion real, solo uso interno)
- En el futuro se puede anadir API key real si se expone a Internet

---

## 📡 Protocolo de Conexion

### Desde cualquier proyecto al Gateway
```python
# Python
BASE_URL = "http://100.105.27.27:9000/v1"  # Via Tailscale
# o
BASE_URL = "http://192.168.1.42:9000/v1"    # Via LAN (misma red)
```

### CORS Bypass (frontend local → backend Madrid)
1. Usar **Tailscale** para visibilidad
2. Configurar **Vite Proxy** en `vite.config.js`:
   ```javascript
   server: {
     proxy: { '/api': 'http://100.105.27.27:9000' }
   }
   ```
3. En frontend, usar rutas relativas: `fetch('/api/v1/chat/completions', ...)`

### Desde Europa Scraper (SERVIDOR01)
```python
ollama_url = "http://192.168.1.42:11434"  # LAN directa (misma red)
gateway_url = "http://192.168.1.42:9000/v1"  # LAN directa al Gateway
```

---

## 🛠️ Comandos de Gestion

### Systemd Services (Madrid)
```bash
# ComfyUI
sudo systemctl {start|stop|restart|status} comfyui
journalctl -u comfyui -f

# Wan2GP
sudo systemctl {start|stop|restart|status} wan2gp
journalctl -u wan2gp -f

# AI Hub Gateway
sudo systemctl {start|stop|restart|status} ai-hub-gateway
journalctl -u ai-hub-gateway -f

# Piper TTS
sudo systemctl {start|stop|restart|status} tts
journalctl -u tts -f

# Whisper STT
sudo systemctl {start|stop|restart|status} stt
journalctl -u stt -f

# Avatar Services (Hallo2, LatentSync, LivePortrait, MuseTalk)
sudo systemctl {start|stop|restart|status} ai-avatars
journalctl -u ai-avatars -f

# Effects Services (Rembg, Real-ESRGAN, Higgsfield)
sudo systemctl {start|stop|restart|status} ai-effects
journalctl -u ai-effects -f
```

### Docker Services (Madrid)
```bash
# DocuMusic
cd ~/documusic && docker compose {up -d|down|restart|logs}

# AI Hub Studio (portal)
docker ps --filter name=ai-hub-studio
docker restart ai-hub-studio
```

### Ollama
```bash
# Listar modelos instalados
ollama list

# Descargar nuevo modelo
ollama pull mistral

# Eliminar modelo
ollama rm modelo_name
```

### Servicios Python (Avatares, Efectos, Video)
```bash
# Ver servicios corriendo
ps aux | grep -E 'serve_avatars|ai-effects|cogvideox_svc|storydiffusion_svc'

# Logs
tail -f /tmp/serve_avatars.log /tmp/ai-effects.log
```

---

## 📝 Notas para Agentes de IA

### Si eres un agente de desarrollo (Cline, Cursor, etc.):
1. **Antes de crear un proyecto nuevo**, consulta `GET /v1/models` para saber que modelos tienes disponibles
2. **Para conectar al Gateway**, usa `http://100.105.27.27:9000/v1` como base_url
3. **Para LLM**, usa el formato OpenAI compatible (no hace falta aprender API de Ollama)
4. **No pagues tokens** - todo corre localmente en la RTX 5080
5. **Si necesitas un modelo nuevo**, anadelo al `MODEL_CATALOG.md` y al `model_registry.yaml`
6. **El portal AI Hub Studio** esta en `http://100.105.27.27:3000` - consulta ahi las herramientas disponibles

### Actualizar el portal:
```bash
cd ai-hub-studio && python deploy.py
```

### MCP Servers (acceso desde Cline/Cursor):
- **ai-hub-gateway** (`C:\Users\julio\Documents\Cline\MCP\ai-hub-mcp\server.py`) - Chat, status, modelos, gestion de servicios
- **comfyui** (`C:\Users\julio\Documents\Cline\MCP\comfyui-mcp-server\server.py`) - Generacion de imagenes, audio, video via ComfyUI workflows

### Convenciones:
- Un modelo = una ubicacion canonica en `/mnt/seagate/models/`
- Symlinks en `/mnt/seagate/links/` para cada herramienta
- `model_registry.yaml` es la fuente de verdad para el Gateway
- NO mover modelos directamente - usar scripts de reestructuracion
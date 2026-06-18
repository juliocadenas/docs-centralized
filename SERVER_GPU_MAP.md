# 🗺️ Mapa de Infraestructura AI - Servidor Madrid

Este documento sirve como contexto maestro para agentes de IA. Describe la arquitectura, ubicación de modelos y flujos de trabajo del servidor de producción.

## 🖥️ Servidor: Madrid (NAB9 - Pop!_OS)
- **IP Tailscale:** `100.105.27.27` (cuenta `juliocadenas@gmail.com`) ✅ **ONLINE** - Todos los servicios operativos
- **IP LAN:** `192.168.1.42`
- **Hardware:** NVIDIA GeForce RTX 5080 (16GB VRAM) + OCuLink eGPU (DEG2)
- **SO:** Linux Pop!_OS 22.04 LTS
- **RAM:** 32GB
- **Disco Local:** 220GB SSD (sda) - Sistema operativo + Docker
- **Disco USB 3:** Seagate 1.8TB (sdb) → `/mnt/seagate` - **AI Hub centralizado**
- **Entorno:** Docker + NVIDIA Container Toolkit (CUDA 12.1)
- **Usuario:** `pepe` / `pepe1234`

---

## 💾 AI Hub Centralizado (Seagate 1.8TB USB 3)
Todos los modelos de IA están centralizados en el disco USB 3 de 1.8TB, organizados en estructura canónica con symlinks para compatibilidad.

- **Dispositivo:** `/dev/sdb1` (label: Seagate2TB)
- **UUID:** `90322c7c-47bb-4302-8335-a77adc7e4fa5`
- **Montaje:** `/mnt/seagate` (fstab persistente con `nofail`)
- **Espacio:** 1.8TB total, 1.6TB libre (104GB usados)
- **Symlink:** `~/AI_MODELS` → `/mnt/seagate` (backward compatibility)

### Estructura Canónica (reestructurada 26 mayo 2026):
```
/mnt/seagate/
├── models/                          # ✦ ALMACÉN CANÓNICO - NO reorganizar sin actualizar symlinks
│   ├── audio/                       # 56GB - Modelos de audio
│   │   ├── music_generation/        # Generación de música
│   │   │   ├── YuE-s1/              # (~12GB) YuE Stage 1
│   │   │   ├── YuE-s2/              # (~3.7GB) YuE Stage 2
│   │   │   ├── ACE-Step-v1-3.5B/    # (~7.8GB) ACE-Step
│   │   │   ├── HeartMuLa/           # (~21GB) HeartMuLa + HeartCodec
│   │   │   └── DiffRhythm2/         # (~4.8GB) DiffRhythm v2
│   │   ├── codecs/                  # Codecs de audio
│   │   │   ├── xcodec_mini_infer/   # (~1.8GB) XCodec
│   │   │   ├── MuQ-large-msd-iter/  # (~1.3GB) MuQ MSD
│   │   │   └── MuQ-MuLan-large/     # (~2.5GB) MuQ MuLan
│   │   └── language/                # Modelos de lenguaje para audio
│   │       └── xlm-roberta-base/    # (~1.1GB) XLM-RoBERTa
│   ├── vision/                      # 49GB - Modelos de video/imagen
│   │   ├── checkpoints/             # Checkpoints principales
│   │   │   ├── wan2.1_t2v_1.3b/     # (~5.3GB) WAN 2.1 T2V 1.3B
│   │   │   ├── ltx-video/           # (~6.3GB) LTX Video v0.9.8
│   │   │   ├── hunyuan-video/       # (~25.6GB) HunyuanVideo T2V
│   │   │   └── v1-5-pruned-emaonly.safetensors  # (~4GB) SD v1.5
│   │   ├── text_encoders/           # Text encoders
│   │   │   └── t5xxl_fp8_e4m3fn.safetensors  # (~4.6GB) T5 XXL FP8
│   │   ├── clip/                    # CLIP models
│   │   │   ├── clip_l.safetensors   # (~235MB) CLIP L
│   │   │   └── clip_g.safetensors   # (~2.4GB) CLIP Vision G
│   │   ├── vae/                     # VAE models
│   │   │   └── hunyuan_video_vae_bf16.safetensors  # (~471MB)
│   │   ├── controlnet/              # ControlNet (OpenPose, Canny, Depth)
│   │   ├── ip_adapter/              # IP-Adapter models
│   │   ├── loras/                   # LoRAs para video
│   │   ├── animatediff/             # AnimateDiff models
│   │   ├── embeddings/              # Textual inversion embeddings
│   │   ├── unet/                    # UNet models
│   │   └── upscale_models/          # Upscale/ESRGAN models
│   └── llm/                         # Modelos de lenguaje (Ollama)
├── links/                           # ✦ SYMLINKS DE COMPATIBILIDAD
│   ├── comfyui/                     # → ComfyUI extra_model_paths.yaml
│   │   ├── checkpoints → ../../models/vision/checkpoints
│   │   ├── clip → ../../models/vision/clip
│   │   ├── vae → ../../models/vision/vae
│   │   ├── text_encoders → ../../models/vision/text_encoders
│   │   ├── controlnet → ../../models/vision/controlnet
│   │   ├── ipadapter → ../../models/vision/ip_adapter
│   │   ├── loras → ../../models/vision/loras
│   │   └── ... (14 symlinks total)
│   └── huggingface/                 # → HuggingFace cache compatibility
│       ├── YuE-s1 → ../../models/audio/music_generation/YuE-s1
│       ├── ACE-Step-v1-3.5B → ../../models/audio/music_generation/ACE-Step-v1-3.5B
│       └── ... (9 symlinks total)
├── api/                             # APIs y registry
│   └── model_registry.yaml          # Catalog central de todos los modelos
├── audio/                           # Legacy audio paths (mantener)
├── llm/                             # Legacy LLM paths
├── cache/                           # Cache común de inferencia
├── backup/                          # Backups locales
├── output/                          # Output de ComfyUI
├── input/                           # Input de ComfyUI
└── local_backup/                    # Source code repos (~479MB, solo código)
```

### Model Registry
El archivo `/mnt/seagate/api/model_registry.yaml` contiene el catálogo centralizado de todos los modelos con metadata (formato, tamaño, tipo, status). Todas las apps (DocuMusic, ComfyUI, futuros proyectos) deben consultar este archivo.

### local_backup/ - Source Code & Repos (montados por Docker)
```
/mnt/seagate/local_backup/
├── ace-step/          # → Docker: /opt/ACE-Step (ACE-Step source code)
├── DiffRhythm2/       # → Docker: /opt/DiffRhythm2 (DiffRhythm v2 source)
├── heartlib/          # → Docker: /opt/heartlib (HeartMuLa source code)
├── yue/               # → Docker: /opt/YuE (YuE source code + xcodec)
├── ollama/            # → Docker Ollama: /root/.ollama (modelos Ollama)
└── DiffRhythm-v1/     # DiffRhythm v1 (legacy)
```
### Modelos Actuales (104GB total):

**Audio (56GB):**
| Modelo | Path Canónico | Tamaño | Tipo |
|--------|--------------|--------|------|
| YuE Stage 1 | `/mnt/seagate/models/audio/music_generation/YuE-s1` | 12GB | text-to-music |
| YuE Stage 2 | `/mnt/seagate/models/audio/music_generation/YuE-s2` | 3.7GB | music-refinement |
| ACE-Step v1 3.5B | `/mnt/seagate/models/audio/music_generation/ACE-Step-v1-3.5B` | 7.8GB | text-to-music |
| HeartMuLa 3B | `/mnt/seagate/models/audio/music_generation/HeartMuLa` | 21GB | text-to-music |
| DiffRhythm v2 | `/mnt/seagate/models/audio/music_generation/DiffRhythm2` | 4.8GB | text-to-music |
| XCodec Mini | `/mnt/seagate/models/audio/codecs/xcodec_mini_infer` | 1.8GB | codec |
| MuQ Large MSD | `/mnt/seagate/models/audio/codecs/MuQ-large-msd-iter` | 1.3GB | codec |
| MuQ MuLan | `/mnt/seagate/models/audio/codecs/MuQ-MuLan-large` | 2.5GB | codec |
| XLM-RoBERTa | `/mnt/seagate/models/audio/language/xlm-roberta-base` | 1.1GB | language |

**Vision (49GB):**
| Modelo | Path Canónico | Tamaño | Tipo |
|--------|--------------|--------|------|
| WAN 2.1 T2V 1.3B | `/mnt/seagate/models/vision/checkpoints/wan2.1_t2v_1.3b` | 5.3GB | text-to-video |
| LTX Video v0.9.8 | `/mnt/seagate/models/vision/checkpoints/ltx-video` | 6.3GB | text-to-video |
| HunyuanVideo T2V | `/mnt/seagate/models/vision/checkpoints/hunyuan-video` | 25.6GB | text-to-video |
| SD v1.5 | `/mnt/seagate/models/vision/checkpoints/v1-5-pruned-emaonly.safetensors` | 4GB | text-to-image |
| T5 XXL FP8 | `/mnt/seagate/models/vision/text_encoders/t5xxl_fp8_e4m3fn.safetensors` | 4.6GB | text-encoder |
| CLIP L | `/mnt/seagate/models/vision/clip/clip_l.safetensors` | 235MB | clip |
| CLIP Vision G | `/mnt/seagate/models/vision/clip/clip_g.safetensors` | 2.4GB | clip-vision |
| Hunyuan VAE | `/mnt/seagate/models/vision/vae/hunyuan_video_vae_bf16.safetensors` | 471MB | vae |

---

## 🏢 Servidor NAS: SERVIDOR01 (Proxmox VE)
- **IP LAN:** `192.168.1.210`
- **Hardware:** Debian 12 Proxmox, 2.45TB LVM RAID, 188GB RAM
- **NFS Exports:**
  - `/mnt/ai_models` → `192.168.1.0/24` (montado en NAB9 como backup/herencia)
  - `/srv/comfyui_models` → `192.168.1.0/24` (montado en `/mnt/nfs_models`, 73GB usado)
- **Usuario:** `julio` / `julio@julio` (sudo OK)
- **LVM:** VG `pve` 2.45TB
  - `pve-root`: 112GB
  - `pve/ai_models`: Thin LV 500GB montado en `/mnt/ai_models` (~420GB libre)
- **Estado:** Los modelos ya están migrados al Seagate. NFS se mantiene como backup.
- **Última actualización:** 26 mayo 2026

---

## 🛠️ Herramientas y Librerías Core
- **Inferencia LLM/Música:** `llama-cpp-python` (con soporte CUDA)
- **Backend:** FastAPI (Python 3.10+)
- **Frontend:** React + Vite (con Proxy configurado para evitar CORS)
- **Orquestación:** Docker Compose
- **NLP/Lyrics:** Ollama (puerto 11434)
- **Generación Video/Imagen:** ComfyUI (nativo, venv Python) en puerto 8188

---

## 🚀 Proyectos Activos

### 1. DocuMusic
- **Repositorio:** `~/documusic`
- **Frontend:** React (Vite) en puerto 5173 (local) → Proxy a 8000 (Madrid)
- **Backend:** FastAPI en puerto 8000 (Madrid)
- **Modelos usados:**
  - `YuE` → `/mnt/seagate/models/audio/music_generation/YuE-s1` y `YuE-s2`
  - `ACE-Step` → `/mnt/seagate/models/audio/music_generation/ACE-Step-v1-3.5B`
  - `DiffRhythm` → `/mnt/seagate/models/audio/music_generation/DiffRhythm2`
  - `Llama3 (Ollama)` → Para generación de letras
- **Docker volumes:** Montan `/mnt/seagate/models/audio/` para acceso a modelos

### 2. Wan2GP (Generación Video Nativa - GPU Optimizada)
- **Repositorio:** `/home/pepe/Wan2GP` (clon directo, sin Docker)
- **URL:** `http://100.105.27.27:7860` (Gradio WebUI)
- **Entorno:** Python venv en `~/Wan2GP/venv/` (Python 3.12)
- **PyTorch:** nightly cu132 (CUDA 13.0 para RTX 5080 Blackwell)
- **Modelo base:** WAN 2.1 T2V/I2V + LTX Video + HunyuanVideo (usa modelos de `/mnt/seagate/models/vision/checkpoints/`)
- **Puerto:** 7860 (Gradio WebUI)
- **Servicio:** systemd `wan2gp.service` (enabled, auto-start)
- **Estado:** ✅ **OPERATIVO** - 27 mayo 2026 - Gradio WebUI escuchando en puerto 7860
- **Instalación completada:**
  - ✅ Repo clonado en `/home/pepe/Wan2GP`
  - ✅ Python 3.12 venv creado
  - ✅ PyTorch nightly cu132 instalado (soporte Blackwell RTX 5080)
  - ✅ CUDA 13 runtime libs instaladas
  - ✅ mmgp instalado (VRAM optimizer)
  - ✅ Todas las deps: rembg, optimum, transformers 5.9.0, segment-anything, etc.
  - ✅ Parches aplicados: transformers auto_factory.py + configuration_auto.py (conflictos HiggsAudio)
  - ✅ Wan2GP exist_ok patch aplicado
  - ✅ Systemd service configurado: `--listen --server-port 7860 --server-name 0.0.0.0`
- **VRAM:** Comparte GPU con ComfyUI/DocuMusic (16GB RTX 5080)
- **Ventaja sobre ComfyUI:** Inferencia directa sin overhead de nodos, optimizado para GPUs con poca VRAM
- **Uso principal:** Generación rápida de video T2V/I2V con WAN 2.1, LTX Video, HunyuanVideo

### 3. ComfyUI Video Studio
- **Repositorio:** `/home/pepe/ComfyUI` (clon directo, sin Docker)
- **URL:** `http://100.105.27.27:8188`
- **Entorno:** Python venv en `~/comfyui_env/`
- **Servicio:** systemd `comfyui.service` (auto-start)
- **Config rutas:** `/home/pepe/ComfyUI/extra_model_paths.yaml` → `/mnt/seagate/links/comfyui/`
- **Output:** `/mnt/seagate/output/`
- **Input:** `/mnt/seagate/input/`
- **Estado:** ✅ Operativo - Todos los modelos en Seagate 1.8TB (reestructurado)
- **Uso principal:** Generación de video marketing (TikTok/RRSS) con WAN 2.1 y LTX Video
- **Gestión VRAM:** ComfyUI libera modelos automáticamente. Si DocuMusic necesita VRAM: `sudo systemctl stop comfyui`

---

## 📡 Protocolo de Conexión (CORS Bypass)
Para conectar un frontend local (Venezuela) con el backend de Madrid sin errores de CORS:
1. Usar **Tailscale** para visibilidad de IP
2. Configurar **Vite Proxy** en `vite.config.js`:
   ```javascript
   server: {
     proxy: { '/api': 'http://100.105.27.27:8000' }
   }
   ```
3. En el frontend, usar rutas relativas: `axios.get('/api/status')`

---

## 📝 Notas de Mantenimiento

### DocuMusic (Docker)
- **Actualizar Código:** `git pull origin main && docker compose up -d --build`
- **Ver Logs:** `docker logs documusic_backend --tail 50`
- **Limpiar Docker:** `docker system prune -f` (usar con cuidado)

### Wan2GP (Nativo + systemd)
- **Iniciar:** `sudo systemctl start wan2gp`
- **Detener:** `sudo systemctl stop wan2gp`
- **Estado:** `sudo systemctl status wan2gp`
- **Ver Logs:** `journalctl -u wan2gp -f`
- **Reiniciar:** `sudo systemctl restart wan2gp`
- **Actualizar:** `cd ~/Wan2GP && git pull && sudo systemctl restart wan2gp`
- **Acceder:** `http://100.105.27.27:7860` (via Tailscale)

### ComfyUI (Nativo + systemd)
- **Iniciar:** `sudo systemctl start comfyui`
- **Detener:** `sudo systemctl stop comfyui`
- **Estado:** `sudo systemctl status comfyui`
- **Ver Logs:** `journalctl -u comfyui -f`
- **Reiniciar:** `sudo systemctl restart comfyui`
- **Actualizar:** `cd ~/ComfyUI && git pull && sudo systemctl restart comfyui`
- **Liberar VRAM:** `sudo systemctl stop comfyui`

### Estructura de Modelos (post-reestructuración 26 mayo 2026)
- **Principio:** Un modelo = una ubicación canónica en `/mnt/seagate/models/`
- **Compatibilidad:** Symlinks en `/mnt/seagate/links/` para cada herramienta
- **Registry:** `/mnt/seagate/api/model_registry.yaml` es la fuente de verdad
- **NO mover modelos directamente** - usar scripts de reestructuración
- **Scripts de reestructuración:** `scripts/restructure_seagate_phase1.py`, `phase2.py`, `fix_symlinks.py`

### Puertos en Uso
| Puerto | Servicio | Tipo |
|--------|----------|------|
| 9000 | AI Hub Gateway (FastAPI) | Nativo (systemd) |
| 7860 | Wan2GP Video Generation (Gradio) | Nativo (systemd) |
| 8000 | DocuMusic Backend (FastAPI) | Docker |
| 8188 | ComfyUI Video Studio | Nativo (systemd) |
| 11434 | Ollama LLM | Nativo |
| 5173 | DocuMusic Frontend (Vite) | Local |

---

## 🏢 Servidor: SERVIDOR01 (Xeon 48 núcleos - Europa Scraper)
- **IP Tailscale:** `100.83.253.87` (cuenta `juliocadenas@gmail.com`)
- **IP LAN:** `192.168.1.210` (misma red que NAB9/IA SERVER)
- **Hardware:** Intel Xeon 48 núcleos
- **Cuenta Tailscale:** `juliocadenas@gmail.com`
- **Usuario:** `julio` / `julio@julio`
- **Proyecto:** Europa Scraper v3.1-LIVE
  - **Repo:** `europa-scraper` (GitHub: `juliocadenas/europa-scraper`)
  - **Servidor:** FastAPI en puerto `8001`
  - **Cliente:** Tkinter GUI (Python) — se conecta al servidor via HTTP
  - **Motor de Búsqueda AI:** Google AI Scraper usa Ollama del IA SERVER (NAB9) vía LAN `192.168.1.42:11434` o Gateway `192.168.1.42:9000/v1`

### Integración IA SERVER ↔ SERVIDOR01
```
SERVIDOR01 (Xeon)                     IA SERVER (NAB9 - Pop!_OS)
┌─────────────────────┐               ┌──────────────────────────┐
│ Europa Scraper       │               │ Ollama (LLM local)       │
│ FastAPI :8001        │──LAN HTTP──→ │ http://192.168.1.42:11434│
│ Google AI Scraper    │               │ Modelo: llama3.1         │
│ site:usa.gov         │               │ RTX 5080 16GB VRAM      │
└─────────────────────┘               └──────────────────────────┘
```
- **Comunicación:** LAN directa `192.168.1.42:11434` (no necesita Tailscale, misma red local)
- **Config:** `config.json` → `ai_scraper.ollama_url = "http://192.168.1.42:11434"`
- **ScrapeGraphAI** corre en SERVIDOR01, solo envía prompts a Ollama en NAB9

### Notas Tailscale ✅ Unificado
- **Todos los dispositivos** en cuenta `juliocadenas@gmail.com` (migrado 7 junio 2026)
- **IA SERVER (NAB9):** `100.105.27.27`
- **SERVIDOR01:** `100.83.253.87`
- **PC Julio:** `100.76.38.116`
- **Acceso directo** desde cualquier dispositivo a cualquier otro, sin `tailscale switch`

### MCP Servers (acceso desde Cline/Cursor)
- **ai-hub-gateway** (`C:\Users\julio\Documents\Cline\MCP\ai-hub-mcp\server.py`) - Chat, status, modelos, gestión
- **comfyui** (`C:\Users\julio\Documents\Cline\MCP\comfyui-mcp-server\server.py`) - Generación de imágenes/audio/video


### Montajes de Disco
| Montaje | Dispositivo | Tamaño | Uso |
|---------|-------------|--------|-----|
| `/` | /dev/sda3 (SSD) | 220GB | Sistema + Docker |
| `/mnt/seagate` | /dev/sdb1 (USB 3) | 1.8TB | AI Hub centralizado (104GB usados) |
| `/mnt/ai_models` | NFS (SERVIDOR01) | 492GB | Backup/herencia |
| `/mnt/nfs_models` | NFS (SERVIDOR01) | 110GB | ComfyUI models backup |
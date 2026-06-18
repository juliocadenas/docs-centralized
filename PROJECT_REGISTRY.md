# 📋 Registry de Proyectos - Ecosistema AI Hub Madrid

> Registro centralizado de todos los proyectos y que servicios del AI Hub utilizan.
> Ultima actualizacion: 16 junio 2026

---

## Proyectos Activos

### 0. 🧠 AI Hub Gateway (CORE INFRASTRUCTURE)
- **Ubicacion:** `/home/pepe/ai-hub-gateway` (Madrid), `c:\Users\julio\Documents\Proyectos\IA-HUB-MADRID1\ai-hub-gateway` (PC Julio)
- **Tipo:** FastAPI Gateway (systemd + Docker)
- **Descripcion:** API unificada compatible con OpenAI que centraliza todos los servicios AI
- **Puerto:** :9000
- **Endpoint:** `http://100.105.27.27:9000/v1`
- **Servicios AI que gestiona:**
  - Ollama (LLM) → proxy OpenAI-compatible
  - ComfyUI (Images) → proxy de generacion
  - DocuMusic (Audio) → proxy de generacion
  - Wan2GP (Video) → proxy de generacion
  - Piper TTS (Text-to-Speech) → endpoint OpenAI-compatible
  - Whisper STT (Speech-to-Text) → endpoint OpenAI-compatible
- **Funcionalidades:**
  - GPU Manager (VRAM monitoring, service start/stop)
  - Model Registry dinamico
  - Status/Health endpoints
  - Compatible con OpenAI Python SDK, LangChain, CrewAI, etc.
- **Conexion:** Todos los proyectos usan `http://100.105.27.27:9000/v1` como base_url
- **MCP Servers:** ai-hub-gateway + comfyui (Cline/Cursor integration)

### 0.5. 🌐 AI Hub Studio (PORTAL WEB - NUEVO 8 junio 2026)
- **Ubicacion:** `/mnt/seagate/ai-hub-studio` (NAB9), `c:\Users\julio\Documents\Proyectos\IA-HUB-MADRID1\ai-hub-studio` (PC Julio)
- **Tipo:** Next.js 16 + Docker (nginx)
- **Descripcion:** Portal web Netflix-style que agrupa todas las herramientas del AI Hub
- **Puerto:** :3000
- **URL:** `http://100.105.27.27:3000`
- **Tecnologias:** Next.js 16 (Turbopack), Tailwind CSS, Framer Motion, static export
- **Funcionalidades:**
  - Sidebar colapsable estilo Odoo con 8 categorias
  - 22 herramientas catalogadas con estados (online/installing/planned)
  - iframe embebido para servicios externos (Gradio, FastAPI)
  - Chat inline con Ollama via Gateway
  - Herramientas de Marketing inline (Copy, Posts, Blog, Slogans)
- **Deploy:** `cd ai-hub-studio && python deploy.py` (build Next.js + SCP a NAB9 + Docker build/run)
- **Servicios AI usados:** Gateway :9000, Ollama :11434, ComfyUI :8188, Wan2GP :7860, DocuMusic :8000, Hallo2 :8070, LatentSync :8043, LivePortrait :8044, MuseTalk :8040, CogVideoX :7861, StoryDiffusion :7862, Rembg :8050, Real-ESRGAN :8051

### 1. 🎵 DocuMusic
- **Ubicacion:** `~/documusic` (Madrid), `c:\Users\julio\Documents\Proyectos\documusic` (PC Julio)
- **Tipo:** Web App (React + FastAPI)
- **Descripcion:** Generacion de musica documental con IA
- **Puertos:** Frontend :5173, Backend :8000
- **Servicios AI usados:**
  - YuE (Text-to-Music)
  - ACE-Step (Text-to-Music)
  - DiffRhythm (Text-to-Music)
  - Ollama/llama3.1 (generacion de letras)
- **Conexion:** Docker volumes → `/mnt/seagate/models/audio/`

### 2. 🎬 Wan2GP Video Generation
- **Ubicacion:** `/home/pepe/Wan2GP` (Madrid)
- **Tipo:** Gradio WebUI (nativo, systemd)
- **Descripcion:** Generacion de video optimizada GPU
- **Puerto:** :7860
- **Servicios AI usados:**
  - WAN 2.1 T2V 1.3B (Text-to-Video)
  - LTX Video (Text-to-Video)
  - HunyuanVideo (Text-to-Video)
- **Conexion:** Lee modelos de `/mnt/seagate/models/vision/checkpoints/`

### 3. 🖼️ ComfyUI Video Studio
- **Ubicacion:** `/home/pepe/ComfyUI` (Madrid)
- **Tipo:** Node-based UI (nativo, systemd)
- **Descripcion:** Generacion de imagen/video con nodos
- **Puerto:** :8188
- **Servicios AI usados:**
  - SD v1.5 (Text-to-Image)
  - WAN 2.1, LTX Video, HunyuanVideo (Text-to-Video)
  - T5 XXL, CLIP, VAE (encoders/decoders)
- **Conexion:** Symlinks → `/mnt/seagate/links/comfyui/`

### 4. 🔍 Europa Scraper
- **Ubicacion:** SERVIDOR01 (Proxmox)
- **Tipo:** FastAPI + Tkinter Client
- **Descripcion:** Scraper de datos europeos con busqueda AI
- **Puerto:** :8001
- **Servicios AI usados:**
  - Ollama/llama3.1 (via LAN `192.168.1.42:11434`)
- **Conexion:** ScrapeGraphAI envia prompts a Ollama en Madrid

### 5. 🎭 Servicios de Avatar AI (NUEVO 8 junio 2026)
- **Ubicacion:** `/home/pepe/serve_avatars.py`, `/mnt/seagate/models/hallo2|latsync|liveportrait|musetalk`
- **Tipo:** Python HTTP servers (4 threads)
- **Descripcion:** Interfaces web para herramientas de avatar y lip-sync
- **Puertos:** :8070 (Hallo2), :8043 (LatentSync), :8044 (LivePortrait), :8041 (MuseTalk)
- **Repos clonados:** `/mnt/seagate/hallo2`, `/mnt/seagate/LatentSync`, `/mnt/seagate/LivePortrait`, `/mnt/seagate/MuseTalk`
- **Checkpoints:** 28.9GB total (Hallo2 13GB, LatentSync 7.5GB, LivePortrait 2GB, MuseTalk 6.4GB)
- **Estado:** ✅ ONLINE - LivePortrait y MuseTalk con inferencia real verificada (Gradio en GPU). Hallo2 y LatentSync pendientes
- **Conexion:** Acceso via iframe desde AI Hub Studio (:3000)

### 6. 🔧 Servicios de Efectos (NUEVO 8 junio 2026)
- **Ubicacion:** `/home/pepe/effects_services.py` (NAB9)
- **Tipo:** Python HTTP server (multi-threaded)
- **Descripcion:** Interfaces web para herramientas de edicion y efectos con inferencia REAL
- **Puertos:** :8050 (Rembg), :8051 (Real-ESRGAN), :8052 (Higgsfield AI)
- **Estado:** ✅ ONLINE - Rembg y Real-ESRGAN con inferencia real verificada, Higgsfield pendiente
- **Conexion:** Acceso via iframe desde AI Hub Studio (:3000)

### 6.5. 🗣️ Servicios de Voz - TTS & STT (NUEVO 15 junio 2026)
- **Ubicacion:** `/home/pepe/tts_svc.py` (Piper), `/home/pepe/stt_svc.py` (Whisper)
- **Tipo:** Python FastAPI (systemd services)
- **Descripcion:** Servicios de Text-to-Speech y Speech-to-Text
- **Puertos:** :8010 (Piper TTS), :8020 (Whisper STT)
- **Modelos:**
  - Piper TTS 1.4.2 (voz en_Es-us, CPU, ~63MB)
  - Whisper large-v3 (multi-idioma, GPU, ~3GB VRAM)
- **Estado:** ✅ Operativos y verificados
- **APIs:**
  - TTS: `POST http://100.105.27.27:8010/api/synthesize` (text → WAV)
  - STT: `POST http://100.105.27.27:8020/api/transcribe` (audio → text)
  - STT Status: `GET http://100.105.27.27:8020/api/status`
- **Conexion:** Acceso directo o via Gateway endpoints `/v1/audio/speech` y `/v1/audio/transcriptions`

### 7. 🎬 CogVideoX + StoryDiffusion (NUEVO 8 junio 2026)
- **Ubicacion:** `/tmp/cogvideox_svc.py`, `/tmp/storydiffusion_svc.py`
- **Tipo:** Python HTTP servers
- **Descripcion:** Interfaces web para video generation avanzada
- **Puertos:** :7861 (CogVideoX), :7862 (StoryDiffusion)
- **Estado:** Interfaces HTML ONLINE, pendiente descargar checkpoints
- **Conexion:** Acceso via iframe desde AI Hub Studio (:3000)

---

## Proyectos en Desarrollo (PC Julio)

### 8. 🎬 Screenflix
- **Ubicacion:** `c:\Users\julio\Documents\Proyectos\Screenflix`
- **Tipo:** Web App
- **Descripcion:** Plataforma de video/peliculas
- **Servicios AI planeados:**
  - LLM (chat/recomendaciones)
  - Video generation (trailers)
  - TTS (narracion)

### 9. 🤖 AgenteW
- **Ubicacion:** `c:\Users\julio\Documents\Proyectos\AgenteW`
- **Tipo:** Agente IA
- **Descripcion:** Agente IA conversacional
- **Servicios AI planeados:**
  - LLM (conversacion)
  - TTS (voz)
  - STT (entrada voz)

### 10. 🎵 MusicReader
- **Ubicacion:** `c:\Users\julio\Documents\Proyectos\MusicReader`
- **Tipo:** App
- **Descripcion:** Lectura/procesamiento de musica
- **Servicios AI planeados:**
  - Audio models (analisis)
  - LLM (asistencia)

### 11. ⚰️ Funebre
- **Ubicacion:** `c:\Users\julio\Documents\Proyectos\Funebre`
- **Tipo:** App
- **Descripcion:** Proyecto funerario conmemorativo
- **Servicios AI planeados:**
  - TTS (narracion)
  - Image generation (memoriales)
  - LLM (textos)

### 12. 💃 VanessaEvo
- **Ubicacion:** `c:\Users\julio\Documents\Proyectos\VanessaEvo`
- **Tipo:** App
- **Descripcion:** Evolucion de avatar/danza
- **Servicios AI planeados:**
  - Video generation (danza) ✅ ahora disponible via Wan2GP
  - Lip-sync ✅ ahora disponible via LatentSync/MuseTalk
  - Avatar animation ✅ ahora disponible via Hallo2/LivePortrait
  - TTS

### 13. ⛏️ Minerwatch
- **Ubicacion:** `c:\Users\julio\Documents\Proyectos\Minerwatch`
- **Tipo:** App
- **Descripcion:** Monitoreo de mineria
- **Servicios AI planeados:**
  - Object detection (YOLOv8)
  - LLM (analisis)

### 14. 🎵 Documusicmula
- **Ubicacion:** `c:\Users\julio\Documents\Proyectos\Documusicmula`
- **Tipo:** Variante de DocuMusic
- **Descripcion:** Variante musical de DocuMusic
- **Servicios AI planeados:**
  - Audio generation (YuE, ACE-Step)
  - LLM (letras)

---

## Matriz Proyecto × Servicio AI

| Proyecto | LLM | TTS | STT | Image | Video | Audio | Lip-sync | Avatar | Efectos | Detection | Gateway |
|----------|-----|-----|-----|-------|-------|-------|----------|--------|---------|-----------|---------|
| **AI Hub Gateway** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | - | - | **CORE** |
| **AI Hub Studio** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | - | **PORTAL** |
| DocuMusic | ✅ | - | - | - | - | ✅ | - | - | - | - | 🔜 |
| Wan2GP | - | - | - | - | ✅ | - | - | - | - | - | - |
| ComfyUI | - | - | - | ✅ | ✅ | - | - | - | - | - | - |
| Europa Scraper | ✅ | - | - | - | - | - | - | - | - | - | - |
| Avatar Services | - | - | - | - | - | - | ✅ | ✅ | - | - | - |
| Voice Services (TTS/STT) | - | ✅ | ✅ | - | - | - | - | - | - | - | - |
| Screenflix | 🔜 | 🔜 | - | 🔜 | ✅ | - | 🔜 | 🔜 | - | - | - |
| AgenteW | 🔜 | 🔜 | 🔜 | - | - | - | - | - | - | - | - |
| MusicReader | 🔜 | - | 🔜 | - | - | 🔜 | - | - | - | - | - |
| Funebre | 🔜 | 🔜 | - | 🔜 | - | - | - | - | - | - | - |
| VanessaEvo | 🔜 | 🔜 | - | - | ✅ | ✅ | ✅ | ✅ | - | - | - |
| Minerwatch | 🔜 | - | - | - | - | - | - | - | - | 🔜 | - |

---

## Como Registrar un Proyecto Nuevo

1. Anadir entrada en este archivo con nombre, ubicacion, tipo, descripcion
2. Listar los servicios AI que usa o planea usar
3. Actualizar la matriz Proyecto × Servicio
4. Anadir `.clinerules` al proyecto apuntando al `INFRASTRUCTURE_MAP.md`
5. Si el proyecto necesita nuevos modelos, actualizar `MODEL_CATALOG.md`
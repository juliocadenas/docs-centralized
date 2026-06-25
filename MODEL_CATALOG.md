# 📦 Catalogo de Modelos AI - Hub Madrid

> Fuente de verdad para modelos disponibles y planificados.
> Ultima actualizacion: 21 junio 2026 (Qwen2.5-VL + nomic-embed-text instalados + fixes async bugs)

---

## ✅ Modelos Instalados y Operativos

### LLM (Large Language Models)
| Modelo | ID | Tipo | VRAM | Puerto | Estado |
|--------|-----|------|------|--------|--------|
| Qwen 2.5 14B | `qwen2.5:14b` | Chat/Multilingue/Calidad | ~8GB | 11434 (Ollama) | ✅ Activo (25 jun 2026) |
| Gemma 2 9B | `gemma2:9b` | Chat/Instruct | ~5.5GB | 11434 (Ollama) | ✅ Activo (25 jun 2026) |
| Llama 3.1 8B | `llama3.1` | Chat/Instruct | ~5GB | 11434 (Ollama) | ✅ Activo |
| Llama 3.2 3B | `llama3.2:3b` | Chat/Rapido | ~2GB | 11434 (Ollama) | ✅ Activo (25 jun 2026) |
| Qwen 2.5 7B | `qwen2.5:7b` | Chat/Instruct/Multilingue | ~5GB | 11434 (Ollama) | ✅ Activo (INSTALADO 19 jun 2026) |
| Qwen 2.5 Coder 7B | `qwen2.5-coder:7b` | Programacion/Code | ~5GB | 11434 (Ollama) | ✅ Activo (INSTALADO 19 jun 2026) |
| Qwen 2.5 VL 7B | `qwen2.5vl:7b` | Vision/Multimodal | ~6GB | 11434 (Ollama) | ✅ Activo (INSTALADO 21 jun 2026) |
| Nomic Embed Text | `nomic-embed-text` | Embeddings | ~0.3GB | 11434 (Ollama) | ✅ Activo (INSTALADO 21 jun 2026) |

> **Nota sobre Qwen 2.5:** Modelo de Alibaba, superior a Llama 3.1 en razonamiento, español y codigo.
> Se puede usar via Gateway: `model="qwen2.5:7b"` o `model="qwen2.5-coder:7b"` (incluyendo el tag `:7b`)
>
> **Qwen 2.5 VL (Vision-Language):** Modelo multimodal - puede analizar imágenes.
> Usar via `/v1/chat/completions` con `images` en el mensaje (formato OpenAI Vision).
>
> **Nomic Embed Text:** Genera embeddings (vectores) de texto para RAG/búsqueda semántica.
> Usar via `POST /v1/embeddings` con `model="nomic-embed-text"`.

### � Avatares & Lip-sync (INSTALADO 8 junio 2026)
| Modelo | ID | Tipo | VRAM | Puerto | Path | Estado |
|--------|-----|------|------|--------|------|--------|
| Hallo2 (Fudan) | `hallo2` | Foto+Audio→Video | ~6GB | 8070 | `/mnt/seagate/models/hallo2/` | ✅ Activo |
| LatentSync (ByteDance) | `latentsync` | Lip-sync perfecto | ~4GB | 8043 | `/mnt/seagate/models/latentsync/` | ✅ Activo |
| LivePortrait (KwaiVGI) | `liveportrait` | Animacion facial | ~4GB | 8044 | `/mnt/seagate/models/liveportrait/` | ✅ Activo |
| MuseTalk (TME) | `musetalk` | Lip-sync tiempo real | ~4GB | 8040 | `/mnt/seagate/models/musetalk/` | ✅ Activo |

### �🎬 Video Generation Avanzada
| Modelo | ID | Tipo | VRAM | Puerto | Path | Estado |
|--------|-----|------|------|--------|------|--------|
| CogVideoX (THUDM) | `cogvideox` | Video HQ | ~12GB | 7861 | `/mnt/seagate/CogVideoX/` | ❌ Fallido (requiere re-instalar) |
| StoryDiffusion | `storydiffusion` | Comic→Video | ~6GB | 7862 | `/mnt/seagate/StoryDiffusion/` | ❌ Fallido (requiere re-instalar) |

### 🎙️ Voz (TTS/STT) (VERIFICADO 19 junio 2026)
| Modelo | ID | Tipo | VRAM | Puerto | Estado |
|--------|-----|------|------|--------|--------|
| Piper TTS | `piper_tts` | Text-to-Speech (CPU) | ~0GB | 8010 | ✅ Activo (always-on) |
| Whisper STT | `whisper_stt` | Speech-to-Text | ~2GB | 8020 | ✅ Activo (always-on) |

### 🔧 Efectos & Edicion (VERIFICADO 19 junio 2026)
| Modelo | ID | Tipo | VRAM | Puerto | Path | Estado |
|--------|-----|------|------|--------|------|--------|
| Rembg | `rembg` | Quitar fondo | ~0.5GB | 8050 | `effects_svc` | ✅ Activo |
| Real-ESRGAN | `realesrgan` | Upscale 4x | ~0.5GB | 8051 | `effects_svc` | ✅ Activo |
| Higgsfield AI | `higgsfield` | Efectos video | ~2GB | 8052 | `effects_svc` | ✅ Activo |

### Audio / Musica
| Modelo | ID | Tipo | VRAM | Puerto | Path |
|--------|-----|------|------|--------|------|
| YuE s1+s2 | `yue` | Text-to-Music | ~8GB | 8000 | `/mnt/seagate/models/audio/music_generation/YuE-s1` |
| ACE-Step v1 3.5B | `ace-step` | Text-to-Music | ~4GB | 8000 | `/mnt/seagate/models/audio/music_generation/ACE-Step-v1-3.5B` |
| DiffRhythm v2 | `diffrhythm` | Text-to-Music | ~4GB | 8000 | `/mnt/seagate/models/audio/music_generation/DiffRhythm2` |
| HeartMuLa 3B | `heartmula` | Text-to-Music | ~8GB | - | `/mnt/seagate/models/audio/music_generation/HeartMuLa` |
| XCodec Mini | `xcodec` | Audio Codec | - | - | `/mnt/seagate/models/audio/codecs/xcodec_mini_infer` |
| MuQ Large | `muq` | Audio Encoder | - | - | `/mnt/seagate/models/audio/codecs/MuQ-large-msd-iter` |

### Vision / Imagen / Video
| Modelo | ID | Tipo | VRAM | Puerto | Path |
|--------|-----|------|------|--------|------|
| WAN 2.1 T2V 1.3B | `wan2.1` | Text-to-Video | ~6GB | 7860/8188 | `/mnt/seagate/models/vision/checkpoints/wan2.1_t2v_1.3b` |
| LTX Video v0.9.8 | `ltx-video` | Text-to-Video | ~6GB | 7860/8188 | `/mnt/seagate/models/vision/checkpoints/ltx-video` |
| HunyuanVideo T2V | `hunyuan` | Text-to-Video | ~12GB | 8188 | `/mnt/seagate/models/vision/checkpoints/hunyuan-video` |
| SD v1.5 | `sd15` | Text-to-Image | ~2GB | 8188 | `/mnt/seagate/models/vision/checkpoints/v1-5-pruned-emaonly.safetensors` |
| T5 XXL FP8 | `t5xxl` | Text Encoder | - | - | `/mnt/seagate/models/vision/text_encoders/t5xxl_fp8_e4m3fn.safetensors` |
| CLIP L | `clip-l` | CLIP | - | - | `/mnt/seagate/models/vision/clip/clip_l.safetensors` |
| CLIP Vision G | `clip-g` | CLIP Vision | - | - | `/mnt/seagate/models/vision/clip/clip_g.safetensors` |
| Hunyuan VAE | `hunyuan-vae` | VAE | - | - | `/mnt/seagate/models/vision/vae/hunyuan_video_vae_bf16.safetensors` |

---

## 🔜 Modelos Planificados (Por Instalar)

### Prioridad ALTA

| Modelo | ID | Tipo | VRAM | Puerto | HuggingFace ID | Uso |
|--------|-----|------|------|--------|----------------|-----|
| XTTS-v2 | `xtts-v2` | TTS con voice cloning | ~3GB | **8011** | `coqui/XTTS-v2` | TTS multilingue | 🔧 Docker listo |
| Fish Speech | `fish-speech` | TTS natural | ~3GB | **8012** | `fishaudio/fish-speech-1.5` | TTS alternativo | 🔧 Docker listo |
| OmniVoice Studio | `omnivoice` | TTS 646 idiomas + clonación | ~4GB | **8030** | `OmniVoice Studio` | TTS multilingue avanzado | 🔧 Docker listo |
| Open-Sora | `open-sora` | Text-to-Video | ~10GB | 7863 | `hpcai-tech/Open-Sora` | Video generation tipo Sora (open source) |

### 🤖 Humanos Digitales & VTubers (Prioridad MEDIA)

| Modelo | ID | Tipo | VRAM | Puerto | HuggingFace ID | Uso |
|--------|-----|------|------|--------|----------------|-----|
| AI-VTuber | `ai-vtuber` | VTuber Pipeline | ~4GB | 8081 | (composicion) | VTuber con IA: TTS + Live2D + Stream |
| Humano Digital | `digital-human` | Full Pipeline | ~8GB | 8082 | (composicion) | LLM + TTS + Lip-sync + Animacion completo |

### 🔧 Vision & Utilidades (Prioridad MEDIA)

| Modelo | ID | Tipo | VRAM | Puerto | HuggingFace ID | Uso |
|--------|-----|------|------|--------|----------------|-----|
| Meta SAM2 | `sam2` | Segmentacion | ~4GB | 8030 | `facebook/sam2.1-hiera-large` | Segmentar objetos en video/imagen |
| InsightFace | `insightface` | Face Recognition | ~2GB | 8050 | `deepinsight/insightface` | Reconocimiento facial |
| DWpose | `dwpose` | Pose Detection | ~2GB | 8061 | `yzd-v/DWPose` | Motion control / pose estimation |

### Prioridad BAJA

| Modelo | ID | Tipo | VRAM | Puerto | HuggingFace ID | Uso |
|--------|-----|------|------|--------|----------------|-----|
| SadTalker | `sadtalker` | Lip-sync | ~4GB | 8041 | `vinthony/SadTalker` | Lip-sync alternativo |
| Wav2Lip | `wav2lip` | Lip-sync ligero | ~2GB | 8042 | `Rudrabha/Wav2Lip` | Lip-sync rapido y ligero |
| YOLOv8 | `yolov8` | Object Detection | ~2GB | 8060 | `ultralytics/yolov8` | Deteccion objetos |
| Llama 3.1 70B | `llama3.1-70b` | LLM Large | ~16GB | 11434 | (Ollama quantized) | LLM mas potente (requiere offload) |

---

## 📊 Resumen de Recursos

### Almacenamiento Usado
- Audio: 56GB
- Vision: 49GB
- Avatares (checkpoints): 28.9GB (Hallo2 13GB + LatentSync 7.5GB + LivePortrait 2GB + MuseTalk 6.4GB)
- LLM: ~37GB (+ Qwen 2.5 14B 8GB + Gemma 2 9B 5.5GB + Llama 3.2 3B 2GB)
- **Total: ~175GB de 1.8TB (9.7%)**

### VRAM por Perfil
| Perfil | Servicios | VRAM Total |
|--------|-----------|------------|
| Desarrollo | Ollama + ComfyUI | ~6-8GB |
| Video | Wan2GP + Ollama | ~12-16GB |
| Audio/Musica | DocuMusic + Ollama | ~8-12GB |
| Avatar | Hallo2 + LatentSync + Ollama | ~14-16GB |
| Lip-sync | MuseTalk + TTS + Ollama | ~9-11GB |
| Video HQ | CogVideoX + Ollama | ~16GB (full) |
| VTuber | AI-VTuber (TTS+Live2D+Ollama) | ~8-10GB |
| Deteccion | YOLO + InsightFace + Ollama | ~8GB |

---

## 🔄 Como Anadir un Modelo Nuevo

1. **Anadir entrada en este archivo** (`MODEL_CATALOG.md`)
2. **Actualizar `model_registry.yaml`** en `/mnt/seagate/api/`
3. **Descargar modelo** a la ruta canonica en `/mnt/seagate/models/{categoria}/`
4. **Crear symlinks** en `/mnt/seagate/links/` si es necesario
5. **Crear wrapper Docker/FastAPI** usando el template en `templates/docker-model-template/`
6. **Anadir al docker-compose** del Gateway
7. **Registrar en el Gateway** como nuevo servicio enrutable
8. **Actualizar el portal** en `ai-hub-studio/src/app/page.tsx` y hacer deploy con `python deploy.py`
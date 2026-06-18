# 📦 Catalogo de Modelos AI - Hub Madrid

> Fuente de verdad para modelos disponibles y planificados.
> Ultima actualizacion: 8 junio 2026

---

## ✅ Modelos Instalados y Operativos

### LLM (Large Language Models)
| Modelo | ID | Tipo | VRAM | Puerto | Estado |
|--------|-----|------|------|--------|--------|
| Llama 3.1 | `llama3.1` | Chat/Instruct | ~4GB | 11434 (Ollama) | ✅ Activo |

### 🎭 Avatares & Lip-sync (INSTALADO 8 junio 2026)
| Modelo | ID | Tipo | VRAM | Puerto | Path | Estado |
|--------|-----|------|------|--------|------|--------|
| Hallo2 (Fudan) | `hallo2` | Foto+Audio→Video | ~6GB | 8070 | `/mnt/seagate/models/hallo2/` | ✅ Activo |
| LatentSync (ByteDance) | `latentsync` | Lip-sync perfecto | ~4GB | 8043 | `/mnt/seagate/models/latentsync/` | ✅ Activo |
| LivePortrait (KwaiVGI) | `liveportrait` | Animacion facial | ~4GB | 8044 | `/mnt/seagate/models/liveportrait/` | ✅ Activo |
| MuseTalk (TME) | `musetalk` | Lip-sync tiempo real | ~4GB | 8040 | `/mnt/seagate/models/musetalk/` | ✅ Activo |

### 🎬 Video Generation Avanzada (INSTALADO 8 junio 2026)
| Modelo | ID | Tipo | VRAM | Puerto | Path | Estado |
|--------|-----|------|------|--------|------|--------|
| CogVideoX (THUDM) | `cogvideox` | Video HQ | ~12GB | 7861 | `/mnt/seagate/CogVideoX/` | 🟡 Instalando |
| StoryDiffusion | `storydiffusion` | Comic→Video | ~6GB | 7862 | `/mnt/seagate/StoryDiffusion/` | 🟡 Instalando |

### 🔧 Efectos & Edicion (INSTALADO 8 junio 2026)
| Modelo | ID | Tipo | VRAM | Puerto | Path | Estado |
|--------|-----|------|------|--------|------|--------|
| Rembg | `rembg` | Quitar fondo | ~1GB | 8050 | `pip: rembg` | 🟡 Instalando |
| Real-ESRGAN | `realesrgan` | Upscale 4x | ~4GB | 8051 | `pip: realesrgan` | 🟡 Instalando |
| Higgsfield AI | `higgsfield` | Efectos video | ~4GB | 8052 | (planificado) | 🟡 Instalando |

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
| XTTS-v2 | `xtts-v2` | TTS | ~3GB | 8010 | `coqui/XTTS-v2` | Text-to-Speech multilingue |
| Whisper large-v3 | `whisper-v3` | STT | ~3GB | 8020 | `openai/whisper-large-v3` | Speech-to-Text |
| Fish Speech | `fish-speech` | TTS | ~3GB | 8010 | `fishaudio/fish-speech-1.5` | TTS alternativo |
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
- LLM: ~5GB
- **Total: ~139GB de 1.8TB (7.5%)**

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
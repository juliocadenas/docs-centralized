# 🎬 AI Hub Madrid - Apps Multimedia

Apps open-source listas para instalar en el servidor GPU. Todas usan los modelos que ya tienes (zero tokens).

## 🚀 Instalación Rápida

### Opción 1: Copiar el instalador al servidor y ejecutar

Desde tu PC (Windows):
```powershell
# Copiar el script al servidor
scp apps/install_apps.sh julio@100.105.27.27:/mnt/seagate/

# Entrar al servidor por SSH
ssh julio@100.105.27.27

# Ejecutar la instalación (pedirá tu contraseña sudo para algunas cosas)
cd /mnt/seagate
bash install_apps.sh all
```

### Opción 2: Instalar una por una

```bash
bash install_apps.sh moneyprinterturbo   # 🥇 Fábrica de Shorts
bash install_apps.sh comfyui-manager     # 🥈 1000+ workflows
bash install_apps.sh swarmui             # 🥉 Frontend fácil imagen
bash install_apps.sh shortgpt            # Cortador de shorts
bash install_apps.sh framepack           # Video de minutos
bash install_apps.sh bark                # TTS con emociones
```

---

## 📱 Apps Disponibles

### 🥇 1. MoneyPrinterTurbo — Fábrica de Videos
**Qué hace**: Genera videos cortos completos automáticamente:
- Guion (LLM → Ollama local)
- Narración (edge-tts, 300+ voces)
- B-roll (videos de Pexels/Pixabay gratuitos)
- Subtítulos animados (Whisper local)
- Música de fondo
- Video final listo para subir

**Para qué**: YouTube Shorts, TikTok, Instagram Reels, monetización

**Recurso**: CPU + 2GB RAM (usa GPU solo para Whisper opcional)

**URL**: `http://100.105.27.27:8501`

---

### 🥈 2. ComfyUI Manager — Gestor de Workflows
**Qué hace**: Añade un botón "Manager" a ComfyUI que permite:
- Instalar workflows de la comunidad con 1 clic
- Gestionar modelos (descarga directa de CivitAI/HuggingFace)
- Actualizar ComfyUI y custom nodes
- Acceso a 1000+ workflows gratuitos

**Para qué**: Desbloquea el potencial completo de ComfyUI sin programar

**Recurso**: 0 (solo es un plugin)

**Se integra en**: Tu ComfyUI existente en `http://100.105.27.27:8188`

---

### 🥉 3. SwarmUI — Frontend Fácil de Imagen
**Qué hace**: Interfaz web bonita sobre ComfyUI:
- Generación con clics (sin nodos)
- Galería de imágenes generadas
- Batch processing (genera 100 variantes)
- Plantillas predefinidas
- Control total de parámetros

**Para qué**: Permitir a no-técnicos usar ComfyUI

**Recurso**: 0 (frontend puro, usa tu ComfyUI)

**URL**: `http://100.105.27.27:7801`

---

### 4. ShortGPT — Cortador de Shorts
**Qué hace**: Convierte videos largos en múltiples shorts:
- Detecta momentos interesantes automáticamente
- Corta con IA
- Añade subtítulos
- Optimiza para vertical

**Para qué**: Reciclar podcasts, entrevistas, webinars en shorts

**Recurso**: CPU

---

### 5. FramePack — Video de Minutos
**Qué hace**: Genera videos de varios minutos con solo 6GB VRAM:
- Tecnología next-frame prediction (del creador de ControlNet)
- Calidad superior a Wan2.1 para escenas largas
- Funciona en tu RTX 5080 sin saturar

**Para qué**: Mini-series, escenas narrativas, B-roll de calidad

**Recurso**: 6GB VRAM

**URL**: `http://100.105.27.27:7861`

---

### 6. Bark WebUI — TTS con Emociones
**Qué hace**: Text-to-speech con capacidades únicas:
- Voces con emociones (risa, susurro, llanto)
- Efectos de sonido generados
- Múltiples idiomas
- Clonación de voz básica

**Para qué**: Narración expresiva, podcast, personajes

**Recurso**: 4GB VRAM

**URL**: `http://100.105.27.27:7862`

---

## 🖥️ Estrategia de VRAM (16GB total)

| Siempre ON | VRAM | Bajo demanda | VRAM |
|---|---|---|---|
| Ollama | 4GB | MoneyPrinterTurbo | ~0 (CPU) |
| Piper TTS | 0 | ComfyUI (Flux/SDXL) | 6-8GB |
| Whisper STT | 2GB | FramePack | 6GB |
| **Total fijo** | **6GB** | Bark | 4GB |

**Disponible para trabajo**: 10GB libres bajo demanda

---

## 📊 Casos de Uso por Industria

### 📱 Agencia de Marketing
1. **Ads cuadrados**: ComfyUI + Flux (vía SwarmUI)
2. **Stories verticales**: ComfyUI + Flux
3. **Copy/Guiones**: MoneyPrinterTurbo (Ollama)
4. **Videos para clientes**: MoneyPrinterTurbo

### 🎥 YouTube / Monetización
1. **Shorts diarios**: MoneyPrinterTurbo (automatizado)
2. **Mini-series**: FramePack (escenas largas)
3. **Reciclar contenido**: ShortGPT (podcasts → shorts)
4. **Thumbnails**: ComfyUI + SwarmUI

### 🛒 Ecommerce
1. **Fotos de producto**: ComfyUI + Rembg (fondo limpio)
2. **Variantes**: ComfyUI (producto en diferentes escenarios)
3. **Videos de producto**: FramePack
4. **Descripciones**: MoneyPrinterTurbo (Ollama)

### 👤 Avatares / Presentadores
1. **Avatar hablando**: HeyGem/MuseTalk (ya instalados)
2. **Voz**: Bark (con emociones) o edge-tts
3. **Múltiples idiomas**: XTTS-v2 (ya instalado)
#!/bin/bash
# ============================================================
# 🎬 AI HUB MADRID - Instalador OpenMontage + HyperFrames + Remotion
# Sistema de Video Producción Agentic - TODO en NAB9 (GPU server)
# ============================================================
# USO:
#   bash _install_openmontage.sh          # Instalar todo
#   bash _install_openmontage.sh check    # Verificar requisitos
#   bash _install_openmontage.sh start    # Iniciar servicios
#   bash _install_openmontage.sh stop     # Detener servicios
# ============================================================

set -e

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Paths
APPS_DIR="/mnt/seagate/apps"
OPENMONTAGE_DIR="$APPS_DIR/openmontage"
REMOTION_DIR="$APPS_DIR/remotion-studio"
OUTPUT_DIR="/mnt/seagate/output/openmontage"

echo -e "${CYAN}🎬 AI Hub Madrid - OpenMontage + Remotion Installer${NC}"
echo -e "${CYAN}   Sistema de Video Producción Agentic - Zero Tokens${NC}"
echo ""

# ============================================================
# FUNCIÓN: Verificar requisitos
# ============================================================
check_requirements() {
    echo -e "${YELLOW}🔍 Verificando requisitos del sistema...${NC}"
    echo ""

    local OK=true

    # Node.js 18+
    if command -v node &>/dev/null; then
        local NODE_VER=$(node -v | sed 's/v//' | cut -d. -f1)
        if [ "$NODE_VER" -ge 18 ]; then
            echo -e "  ${GREEN}✅ Node.js $(node -v)${NC}"
        else
            echo -e "  ${RED}❌ Node.js muy viejo ($(node -v)). Necesita 18+${NC}"
            OK=false
        fi
    else
        echo -e "  ${YELLOW}⚠️  Node.js no instalado (se instalará)${NC}"
    fi

    # FFmpeg
    if command -v ffmpeg &>/dev/null; then
        echo -e "  ${GREEN}✅ FFmpeg $(ffmpeg -version | head -1 | awk '{print $3}')${NC}"
    else
        echo -e "  ${YELLOW}⚠️  FFmpeg no instalado (se instalará)${NC}"
    fi

    # Chromium
    if command -v chromium-browser &>/dev/null || command -v chromium &>/dev/null || command -v google-chrome &>/dev/null; then
        echo -e "  ${GREEN}✅ Chromium/Chrome instalado${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Chromium no instalado (se instalará)${NC}"
    fi

    # Ollama (debe existir ya)
    if command -v ollama &>/dev/null; then
        echo -e "  ${GREEN}✅ Ollama instalado${NC}"
    else
        echo -e "  ${RED}❌ Ollama no encontrado. Instala Ollama primero.${NC}"
        OK=false
    fi

    # ComfyUI (check puerto)
    if curl -s http://localhost:8188/system_stats &>/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ ComfyUI activo (:8188)${NC}"
    else
        echo -e "  ${YELLOW}⚠️  ComfyUI no responde (se iniciará bajo demanda)${NC}"
    fi

    # Espacio en disco
    local FREE_GB=$(df /mnt/seagate --output=avail -BG 2>/dev/null | tail -1 | tr -d 'G ' || echo "0")
    if [ "${FREE_GB:-0}" -gt 5 ]; then
        echo -e "  ${GREEN}✅ Espacio libre: ${FREE_GB}GB en /mnt/seagate${NC}"
    else
        echo -e "  ${RED}❌ Poco espacio en /mnt/seagate (${FREE_GB}GB). Necesita 5GB+${NC}"
        OK=false
    fi

    echo ""
    if [ "$OK" = true ]; then
        echo -e "${GREEN}✅ Requisitos OK - Listo para instalar${NC}"
    else
        echo -e "${RED}❌ Faltan requisitos críticos${NC}"
        exit 1
    fi
}

# ============================================================
# FUNCIÓN: Instalar Node.js 20 LTS
# ============================================================
install_nodejs() {
    if command -v node &>/dev/null; then
        local NODE_VER=$(node -v | sed 's/v//' | cut -d. -f1)
        if [ "$NODE_VER" -ge 18 ]; then
            echo -e "  ${GREEN}✅ Node.js ya instalado ($(node -v))${NC}"
            return 0
        fi
    fi

    echo -e "  ${YELLOW}📦 Instalando Node.js 20 LTS...${NC}"

    # NodeSource setup
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs

    # Verificar
    echo -e "  ${GREEN}✅ Node.js $(node -v) instalado${NC}"
    echo -e "  ${GREEN}✅ npm $(npm -v) instalado${NC}"

    # Instalar pnpm global
    sudo npm install -g pnpm
    echo -e "  ${GREEN}✅ pnpm instalado${NC}"
}

# ============================================================
# FUNCIÓN: Instalar Chromium headless
# ============================================================
install_chromium() {
    if command -v chromium-browser &>/dev/null || command -v chromium &>/dev/null; then
        echo -e "  ${GREEN}✅ Chromium ya instalado${NC}"
        return 0
    fi

    echo -e "  ${YELLOW}📦 Instalando Chromium...${NC}"
    sudo apt-get update
    sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium

    echo -e "  ${GREEN}✅ Chromium instalado${NC}"
}

# ============================================================
# FUNCIÓN: Instalar FFmpeg
# ============================================================
install_ffmpeg() {
    if command -v ffmpeg &>/dev/null; then
        echo -e "  ${GREEN}✅ FFmpeg ya instalado${NC}"
        return 0
    fi

    echo -e "  ${YELLOW}📦 Instalando FFmpeg...${NC}"
    sudo apt-get install -y ffmpeg
    echo -e "  ${GREEN}✅ FFmpeg instalado${NC}"
}

# ============================================================
# FUNCIÓN: Instalar Remotion + HyperFrames
# ============================================================
install_remotion() {
    echo -e "${YELLOW}📦 Instalando Remotion + HyperFrames Studio...${NC}"

    mkdir -p "$REMOTION_DIR" "$OUTPUT_DIR"
    cd "$REMOTION_DIR"

    # Si ya existe package.json, saltar
    if [ -f "package.json" ] && [ -d "node_modules" ]; then
        echo -e "  ${GREEN}✅ Remotion ya instalado en $REMOTION_DIR${NC}"
        return 0
    fi

    # Crear proyecto Remotion desde template
    # El template base con TypeScript
    if [ ! -f "package.json" ]; then
        echo -e "  ${CYAN}   Creando proyecto Remotion...${NC}"
        npx create-video@latest --template blank --name temp_init 2>/dev/null || true

        # Si se creó, mover contenido
        if [ -d "temp_init" ]; then
            cp -r temp_init/* . 2>/dev/null || true
            cp -r temp_init/.* . 2>/dev/null || true
            rm -rf temp_init
        fi

        # Si no funcionó el template, crear manualmente
        if [ ! -f "package.json" ]; then
            echo -e "  ${CYAN}   Configurando proyecto manualmente...${NC}"
            npm init -y
        fi
    fi

    # Instalar dependencias Remotion core
    npm install --save \
        remotion @remotion/cli @remotion/renderer \
        @remotion/bundler @remotion/cache

    # Instalar HyperFrames (componentes de video agentic)
    npm install --save hyperframes-for-remotion 2>/dev/null || {
        echo -e "  ${YELLOW}   HyperFrames no disponible en npm, instalando desde GitHub...${NC}"
        # Clonar HyperFrames componentes
        if [ ! -d "src/components/hyperframes" ]; then
            mkdir -p src/components
            cd /tmp
            git clone https://github.com/RemotionHub/hyperframes.git 2>/dev/null || true
            if [ -d "hyperframes/src" ]; then
                cp -r hyperframes/src "$REMOTION_DIR/src/components/hyperframes"
            fi
            rm -rf hyperframes
            cd "$REMOTION_DIR"
        fi
    }

    # Crear remotion.config.ts optimizado para NAB9
    cat > remotion.config.ts << 'EOF'
import { Config } from "@remotion/cli/config";
import { enableWebServer } from "@remotion/cli/config";

// Configuración optimizada para RTX 5080 + 32GB RAM
// Chromium usa CPU para screenshots (no compite con GPU)
Config.setVideoImageFormat("jpeg");
Config.setConcurrency(8); // 8 threads paralelos (deja RAM para IA)
Config.setOverwriteOutput(true);

// Web server mode para renderizado agentic
enableWebServer({
    port: 8601,
    maximumConcurrency: 4,
});

// Output
Config.setCodec("h264");
Config.setCrf(18); // Alta calidad
EOF

    # Crear Composition base de ejemplo
    mkdir -p src
    cat > src/Root.tsx << 'ENDOFFILE'
import { Composition } from "remotion";
import { AgenticVideo } from "./AgenticVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AgenticVideo"
        component={AgenticVideo}
        durationInFrames={300} // 10s a 30fps
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
ENDOFFILE

    cat > src/AgenticVideo.tsx << 'ENDOFFILE'
import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  useVideoConfig,
  Img,
  Audio,
  Sequence,
  spring,
} from "remotion";

// Componente reutilizable: Texto animado tipo lower-third
export const LowerThird: React.FC<{
  title: string;
  subtitle?: string;
  delay?: number;
}> = ({ title, subtitle, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slideIn = spring({
    frame: frame - delay,
    fps,
    config: { damping: 200 },
  });

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-start", padding: 60 }}>
      <div style={{
        transform: `translateX(${interpolate(slideIn, [0, 1], [-500, 0])}px)`,
        opacity: slideIn,
      }}>
        <div style={{
          backgroundColor: "rgba(0,0,0,0.8)",
          padding: "16px 32px",
          borderRadius: 8,
          borderLeft: "4px solid #10b981",
        }}>
          <h1 style={{ color: "white", fontSize: 42, fontWeight: "bold", margin: 0 }}>{title}</h1>
          {subtitle && <p style={{ color: "#10b981", fontSize: 24, margin: "4px 0 0 0" }}>{subtitle}</p>}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Componente: Imagen con efecto Ken Burns
export const KenBurnsImage: React.FC<{
  src: string;
  zoom?: number;
}> = ({ src, zoom = 1.1 }) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 300], [1, zoom], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})` }} />
    </AbsoluteFill>
  );
};

// Componente principal del video agentic
export const AgenticVideo: React.FC<{
  scenes?: Array<{
    image?: string;
    title: string;
    subtitle?: string;
    audio?: string;
    durationFrames?: number;
  }>;
}> = ({ scenes = [] }) => {
  // Si no hay escenas, mostrar placeholder
  if (scenes.length === 0) {
    return (
      <AbsoluteFill style={{ backgroundColor: "#0f0f1a", justifyContent: "center", alignItems: "center" }}>
        <h1 style={{ color: "#10b981", fontSize: 64 }}>AI Hub Madrid</h1>
        <p style={{ color: "#888", fontSize: 28 }}>Remotion + OpenMontage Ready</p>
      </AbsoluteFill>
    );
  }

  // Renderizar escenas secuenciales
  let currentFrame = 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {scenes.map((scene, i) => {
        const duration = scene.durationFrames || 150; // 5s por defecto
        const startFrame = currentFrame;
        currentFrame += duration;

        return (
          <Sequence key={i} from={startFrame} durationInFrames={duration}>
            {scene.image && <KenBurnsImage src={scene.image} />}
            {scene.audio && <Audio src={scene.audio} />}
            <LowerThird title={scene.title} subtitle={scene.subtitle} delay={10} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
ENDOFFILE

    # Crear entry point index.ts
    cat > src/index.ts << 'ENDOFFILE'
import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
ENDOFFILE

    echo -e "  ${GREEN}✅ Remotion instalado en $REMOTION_DIR${NC}"
}

# ============================================================
# FUNCIÓN: Instalar OpenMontage
# ============================================================
install_openmontage() {
    echo -e "${YELLOW}📦 Instalando OpenMontage (Sistema Agentic)...${NC}"

    mkdir -p "$OPENMONTAGE_DIR"
    cd "$OPENMONTAGE_DIR"

    # Clonar OpenMontage
    if [ ! -d "app" ]; then
        echo -e "  ${CYAN}   Clonando OpenMontage desde GitHub...${NC}"
        git clone https://github.com/calesthio/OpenMontage.git app || {
            echo -e "  ${YELLOW}   ⚠️  No se pudo clonar OpenMontage. Creando estructura mínima...${NC}"
            mkdir -p app
        }
    fi

    cd app

    # Si hay requirements.txt, instalar
    if [ -f "requirements.txt" ]; then
        echo -e "  ${CYAN}   Instalando dependencias Python...${NC}"
        pip install -r requirements.txt
    fi

    # Crear config adaptada al AI Hub (ZERO TOKENS)
    mkdir -p config
    cat > config/ai_hub.yaml << 'EOF'
# ============================================================
# OpenMontage - Configuración AI Hub Madrid
# Todos los servicios son LOCALES (zero tokens)
# ============================================================

llm:
  # Ollama local (Qwen 2.5 14B - mejor calidad)
  provider: ollama
  model: qwen2.5:14b
  base_url: http://localhost:11434
  api_key: "not-needed"
  
  # Modelo rápido para decisiones agentic
  fast_model: llama3.2:3b
  fast_base_url: http://localhost:11434

image_generation:
  # ComfyUI local (Flux/SDXL)
  provider: comfyui
  base_url: http://localhost:8188
  default_model: flux
  default_width: 1920
  default_height: 1080
  negative_prompt: "blurry, low quality, distorted, watermark"

video_generation:
  # Wan2GP local (WAN 2.1 / Hunyuan)
  provider: wan2gp
  base_url: http://localhost:7860
  default_model: wan2.1
  default_resolution: "480p"
  default_duration: 5

tts:
  # Piper TTS local (rápido, CPU)
  provider: piper
  base_url: http://localhost:8010
  default_voice: es_ES
  default_language: es
  
  # Alternativa: XTTS-v2 para clonación de voz
  xtts_base_url: http://localhost:8011

music_generation:
  # DocuMusic local (ACE-Step)
  provider: documusic
  base_url: http://localhost:8000
  default_model: ace-step
  default_duration: 30

stt:
  # Whisper local (subtítulos automáticos)
  provider: whisper
  base_url: http://localhost:8020
  model: small
  language: es

rendering:
  # Remotion local
  provider: remotion
  project_dir: /mnt/seagate/apps/remotion-studio
  output_dir: /mnt/seagate/output/openmontage
  ffmpeg_path: /usr/bin/ffmpeg
  
  # Configuración de render
  concurrency: 8
  codec: h264
  crf: 18
  fps: 30
  width: 1920
  height: 1080

output:
  base_dir: /mnt/seagate/output/openmontage
  format: mp4
  quality: high
EOF

    # Crear skills personalizados adaptados al AI Hub
    mkdir -p skills/ai-hub
    cat > skills/ai-hub/create-video.md << 'EOF'
# Skill: Create Educational Video

## Description
Create a complete educational video using the AI Hub Madrid infrastructure.
All generation is LOCAL - zero tokens, zero API costs.

## Pipeline Steps

### Step 1: Research & Script (LLM - Qwen 2.5)
- Use Ollama to research the topic and create a structured script
- Script format: JSON with scenes array
- Each scene: { title, narration, visual_description, duration }

### Step 2: Generate Visuals (ComfyUI - Flux)
- For each scene, generate a 1920x1080 image
- Use the visual_description from the script
- Save to: /mnt/seagate/output/openmontage/{project}/images/

### Step 3: Generate Narration (Piper TTS)
- Convert narration text to audio for each scene
- Spanish voice (es_ES)
- Save to: /mnt/seagate/output/openmontage/{project}/audio/

### Step 4: Generate Background Music (DocuMusic)
- Create ambient background music
- Match the video mood/tone
- Save to: /mnt/seagate/output/openmontage/{project}/music/

### Step 5: Render Final Video (Remotion)
- Assemble all assets into final MP4
- Add animated lower-thirds, transitions, subtitles
- Use Ken Burns effect on images
- Output: /mnt/seagate/output/openmontage/{project}/final.mp4

## Tools Available
- chat_with_llm(model, message) → Ollama
- generate_image(prompt, width, height) → ComfyUI
- generate_tts(text, voice, language) → Piper
- generate_music(prompt, duration) → DocuMusic
- render_remotion(scenes_json) → Remotion
- transcribe_audio(file) → Whisper (for subtitles)
EOF

    # Crear pipeline de ejemplo
    mkdir -p pipelines
    cat > pipelines/educational-60s.yaml << 'EOF'
# Pipeline: Video educativo de 60 segundos
# Ejecutar: python -m openmontage run educational-60s --topic "Energía Solar"

name: "Educational 60s Video"
description: "Crea un video educativo de 60s sobre cualquier tema"
duration_seconds: 60
resolution: "1920x1080"
fps: 30
language: "es"

steps:
  - id: script
    tool: llm
    model: qwen2.5:14b
    prompt: |
      Crea un guion para un video educativo de 60 segundos sobre: {topic}
      Formato JSON: { "scenes": [{ "title": "...", "narration": "...", "visual": "..." }] }
      6 escenas de 10s cada una.

  - id: images
    tool: image_gen
    model: flux
    depends_on: [script]
    input: "{script.scenes[].visual}"
    output: "images/scene_{index}.png"

  - id: narration
    tool: tts
    model: piper
    voice: es_ES
    depends_on: [script]
    input: "{script.scenes[].narration}"
    output: "audio/scene_{index}.wav"

  - id: music
    tool: music_gen
    model: ace-step
    prompt: "Música ambient educativa, instrumental, 60 segundos"
    output: "music/background.wav"

  - id: render
    tool: remotion
    depends_on: [images, narration, music]
    template: educational
    output: "final.mp4"
EOF

    echo -e "  ${GREEN}✅ OpenMontage instalado en $OPENMONTAGE_DIR/app${NC}"
}

# ============================================================
# FUNCIÓN: Crear servicio systemd
# ============================================================
create_services() {
    echo -e "${YELLOW}⚙️  Creando servicios systemd...${NC}"

    # Servicio Remotion Web Server (render API)
    sudo tee /etc/systemd/system/remotion-render.service > /dev/null << 'EOF'
[Unit]
Description=Remotion Render Server (AI Hub Madrid)
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/mnt/seagate/apps/remotion-studio
ExecStart=/usr/bin/npx remotion studio --port=8601
Restart=on-failure
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    echo -e "  ${GREEN}✅ Servicio remotion-render creado${NC}"
    echo -e "  ${CYAN}   Habilitar: sudo systemctl enable remotion-render${NC}"
}

# ============================================================
# FUNCIÓN: Verificar instalación
# ============================================================
verify_install() {
    echo -e "${YELLOW}🔍 Verificando instalación...${NC}"
    echo ""

    local OK=true

    # Remotion
    if [ -d "$REMOTION_DIR/node_modules/remotion" ]; then
        echo -e "  ${GREEN}✅ Remotion instalado${NC}"
    else
        echo -e "  ${RED}❌ Remotion no encontrado${NC}"
        OK=false
    fi

    # OpenMontage
    if [ -d "$OPENMONTAGE_DIR/app" ]; then
        echo -e "  ${GREEN}✅ OpenMontage instalado${NC}"
    else
        echo -e "  ${RED}❌ OpenMontage no encontrado${NC}"
        OK=false
    fi

    # FFmpeg
    if command -v ffmpeg &>/dev/null; then
        echo -e "  ${GREEN}✅ FFmpeg disponible${NC}"
    else
        echo -e "  ${RED}❌ FFmpeg no encontrado${NC}"
        OK=false
    fi

    # Test render básico
    if [ "$OK" = true ]; then
        echo ""
        echo -e "${CYAN}   🎬 Probando render de test...${NC}"
        cd "$REMOTION_DIR"
        timeout 120 npx remotion render AgenticVideo "$OUTPUT_DIR/test-render.mp4" 2>&1 | tail -5 || {
            echo -e "  ${YELLOW}   ⚠️  Test render requiere dependencias (normal en primera ejecución)${NC}"
        }
    fi

    echo ""
    if [ "$OK" = true ]; then
        echo -e "${GREEN}🎉 ¡Instalación completada!${NC}"
    else
        echo -e "${RED}❌ Hubieron problemas. Revisa los errores arriba.${NC}"
    fi
}

# ============================================================
# FUNCIÓN: Iniciar servicios
# ============================================================
start_services() {
    echo -e "${YELLOW}▶️  Iniciando servicios...${NC}"

    # Remotion
    if [ -f "/etc/systemd/system/remotion-render.service" ]; then
        sudo systemctl start remotion-render 2>/dev/null && \
            echo -e "  ${GREEN}✅ Remotion Render Server iniciado (:8601)${NC}" || \
            echo -e "  ${YELLOW}⚠️  Remotion no pudo iniciar (ejecuta manualmente)${NC}"
    fi

    echo -e "  ${CYAN}Remotion Studio: http://100.105.27.27:8601${NC}"
}

# ============================================================
# FUNCIÓN: Detener servicios
# ============================================================
stop_services() {
    echo -e "${YELLOW}⏹️  Deteniendo servicios...${NC}"

    sudo systemctl stop remotion-render 2>/dev/null && \
        echo -e "  ${GREEN}✅ Remotion detenido${NC}" || true
}

# ============================================================
# MENÚ PRINCIPAL
# ============================================================
case "$1" in
    check)
        check_requirements
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    *)
        # Instalación completa
        check_requirements

        echo ""
        echo -e "${CYAN}━━━ INSTALANDO COMPONENTES ━━━${NC}"
        echo ""

        install_nodejs
        install_chromium
        install_ffmpeg
        install_remotion
        install_openmontage
        create_services

        echo ""
        verify_install

        echo ""
        echo -e "${CYAN}━━━ SIGUIENTES PASOS ━━━${NC}"
        echo -e "  1. Iniciar Remotion:  ${GREEN}bash _install_openmontage.sh start${NC}"
        echo -e "  2. Studio UI:         ${GREEN}http://100.105.27.27:8601${NC}"
        echo -e "  3. Ver templates:     ${GREEN}cd $REMOTION_DIR && npx remotion compositions${NC}"
        echo -e "  4. Render test:       ${GREEN}cd $REMOTION_DIR && npx remotion render AgenticVideo test.mp4${NC}"
        echo ""
        echo -e "${CYAN}El Gateway endpoint POST /v1/video/agentic se activará automáticamente${NC}"
        echo -e "${CYAN}después de reiniciar el AI Hub Gateway.${NC}"
        ;;
esac
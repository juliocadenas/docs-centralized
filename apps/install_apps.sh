#!/bin/bash
# ============================================================
# 🚀 AI HUB MADRID - Instalador de Apps Multimedia
# Ejecutar en el servidor NAB9 como usuario normal
# ============================================================
# USO:
#   bash install_apps.sh moneyprinterturbo   # Instala solo MoneyPrinterTurbo
#   bash install_apps.sh all                  # Instala todas
#   bash install_apps.sh status               # Ver estado de apps
# ============================================================

set -e

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

APPS_DIR="/mnt/seagate/apps"
COMPOSE_FILE="$APPS_DIR/docker-compose.apps.yml"

echo -e "${CYAN}🚀 AI Hub Madrid - Instalador de Apps${NC}"
echo ""

# Crear directorio base
mkdir -p "$APPS_DIR"

# ============================================================
# FUNCIÓN: Instalar MoneyPrinterTurbo
# ============================================================
install_moneyprinterturbo() {
    echo -e "${YELLOW}📦 Instalando MoneyPrinterTurbo (fábrica de videos Shorts/Reels)...${NC}"
    
    local DIR="$APPS_DIR/moneyprinterturbo"
    mkdir -p "$DIR/projects" /mnt/seagate/storage/moneyprinterturbo
    
    cd "$DIR"
    
    # Clonar repo oficial
    if [ ! -d "app" ]; then
        git clone https://github.com/FujiwaraChoki/MoneyPrinterTurbo.git app
    fi
    
    cd app
    
    # Instalar dependencias
    pip install -r requirements.txt
    
    # Crear config adaptada al AI Hub
    cat > config.toml << 'EOF'
[app]
project_basedir = "./"
project_dir = "./projects"
llm_provider_name = "ollama"
llm_model_name = "qwen2.5:7b"

[app.remote_llm_providers."ollama"]
api_base_url = "http://localhost:11434/v1"
llm_provider = "ollama"

[app.tts]
tts_type = "edge-tts"
edge_tts_voice = "es-ES-AlvaroNeural"

[app.subtitle]
whisper_model = "small"
whisper_language = "es"

[app.audio]
remove_silence = true
speech_rate = 1.0
EOF

    # Instalar edge-tts (gratis, sin VRAM)
    pip install edge-tts
    
    echo -e "${GREEN}✅ MoneyPrinterTurbo instalado en $DIR/app${NC}"
    echo -e "${CYAN}   Para iniciar: cd $DIR/app && streamlit run webui/StreamlitUI.py${NC}"
    echo -e "${CYAN}   UI: http://100.105.27.27:8501${NC}"
}

# ============================================================
# FUNCIÓN: Instalar SwarmUI (frontend bonito para ComfyUI)
# ============================================================
install_swarmui() {
    echo -e "${YELLOW}📦 Instalando SwarmUI (frontend fácil para ComfyUI)...${NC}"
    
    local DIR="$APPS_DIR/swarmui"
    mkdir -p "$DIR"
    
    cd "$DIR"
    
    # Clonar repo oficial
    if [ ! -f "launch-linux.sh" ]; then
        git clone https://github.com/mcmonkeyprojects/SwarmUI.git .
    fi
    
    # Configurar para usar ComfyUI existente en el hub
    export SWARM_BACKEND_COMFY_URL="http://localhost:8188"
    
    echo -e "${GREEN}✅ SwarmUI descargado en $DIR${NC}"
    echo -e "${CYAN}   Para iniciar: cd $DIR && bash launch-linux.sh${NC}"
    echo -e "${CYAN}   UI: http://100.105.27.27:7801${NC}"
}

# ============================================================
# FUNCIÓN: Instalar ComfyUI Manager (gestor de workflows)
# ============================================================
install_comfyui_manager() {
    echo -e "${YELLOW}📦 Instalando ComfyUI Manager (1000+ workflows)...${NC}"
    
    # Encontrar instalación de ComfyUI
    local COMFYUI_CUSTOM="/mnt/seagate/comfyui/custom_nodes"
    if [ ! -d "$COMFYUI_CUSTOM" ]; then
        COMFYUI_CUSTOM="$HOME/ComfyUI/custom_nodes"
    fi
    
    if [ -d "$COMFYUI_CUSTOM/ComfyUI-Manager" ]; then
        echo -e "${YELLOW}   ComfyUI Manager ya está instalado${NC}"
    else
        cd "$COMFYUI_CUSTOM"
        git clone https://github.com/ltdrdata/ComfyUI-Manager.git
        echo -e "${GREEN}✅ ComfyUI Manager instalado${NC}"
    fi
    
    echo -e "${CYAN}   Reinicia ComfyUI y verás el botón 'Manager'${NC}"
}

# ============================================================
# FUNCIÓN: Instalar ShortGPT (video largo → shorts)
# ============================================================
install_shortgpt() {
    echo -e "${YELLOW}📦 Instalando ShortGPT (cortador automático de shorts)...${NC}"
    
    local DIR="$APPS_DIR/shortgpt"
    mkdir -p "$DIR"
    
    cd "$DIR"
    
    # ShortGPT se instala como paquete pip
    pip install shortgpt
    
    echo -e "${GREEN}✅ ShortGPT instalado${NC}"
    echo -e "${CYAN}   Para iniciar: shortgpt${NC}"
}

# ============================================================
# FUNCIÓN: Instalar FramePack (video de minutos con poca VRAM)
# ============================================================
install_framepack() {
    echo -e "${YELLOW}📦 Instalando FramePack (video de minutos, 6GB VRAM)...${NC}"
    
    local DIR="$APPS_DIR/framepack"
    mkdir -p "$DIR"
    
    cd "$DIR"
    
    # Clonar repo oficial del creador de ControlNet
    if [ ! -f "demo_gradio.py" ]; then
        git clone https://github.com/lllyasviel/FramePack.git .
    fi
    
    # Instalar dependencias
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ FramePack instalado en $DIR${NC}"
    echo -e "${CYAN}   Para iniciar: cd $DIR && python demo_gradio.py${NC}"
    echo -e "${CYAN}   UI: http://100.105.27.27:7861${NC}"
}

# ============================================================
# FUNCIÓN: Instalar Bark WebUI (TTS con emociones)
# ============================================================
install_bark() {
    echo -e "${YELLOW}📦 Instalando Bark WebUI (TTS con emociones)...${NC}"
    
    local DIR="$APPS_DIR/bark-webui"
    mkdir -p "$DIR"
    
    cd "$DIR"
    
    if [ ! -f "app.py" ]; then
        git clone https://github.com/C0untFloyd/bark-gui.git .
    fi
    
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ Bark WebUI instalado en $DIR${NC}"
    echo -e "${CYAN}   Para iniciar: cd $DIR && python webui.py${NC}"
    echo -e "${CYAN}   UI: http://100.105.27.27:7862${NC}"
}

# ============================================================
# ESTADO
# ============================================================
show_status() {
    echo -e "${CYAN}📊 ESTADO DE APPS INSTALADAS${NC}"
    echo ""
    
    declare -A APPS=(
        ["MoneyPrinterTurbo"]="/mnt/seagate/apps/moneyprinterturbo/app"
        ["SwarmUI"]="/mnt/seagate/apps/swarmui"
        ["ComfyUI-Manager"]="/mnt/seagate/comfyui/custom_nodes/ComfyUI-Manager"
        ["ShortGPT"]="pip:shortgpt"
        ["FramePack"]="/mnt/seagate/apps/framepack"
        ["Bark-WebUI"]="/mnt/seagate/apps/bark-webui"
    )
    
    for app in "${!APPS[@]}"; do
        path="${APPS[$app]}"
        if [[ "$path" == "pip:"* ]]; then
            pkg="${path#pip:}"
            if pip show "$pkg" >/dev/null 2>&1; then
                echo -e "  ${GREEN}✅ $app${NC}"
            else
                echo -e "  ${RED}❌ $app${NC}"
            fi
        else
            if [ -d "$path" ]; then
                echo -e "  ${GREEN}✅ $app${NC} → $path"
            else
                echo -e "  ${RED}❌ $app${NC}"
            fi
        fi
    done
    
    echo ""
    echo -e "${CYAN}GPU VRAM:${NC}"
    nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv,noheader 2>/dev/null || echo "nvidia-smi no disponible"
    
    echo ""
    echo -e "${CYAN}Disco:${NC}"
    df -h /mnt/seagate | tail -1
}

# ============================================================
# MENÚ PRINCIPAL
# ============================================================
case "$1" in
    moneyprinterturbo|mpt)
        install_moneyprinterturbo
        ;;
    swarmui|swarm)
        install_swarmui
        ;;
    comfyui-manager|manager)
        install_comfyui_manager
        ;;
    shortgpt|short)
        install_shortgpt
        ;;
    framepack|frame)
        install_framepack
        ;;
    bark)
        install_bark
        ;;
    all)
        install_comfyui_manager
        install_moneyprinterturbo
        install_swarmui
        install_shortgpt
        install_framepack
        install_bark
        echo ""
        echo -e "${GREEN}🎉 TODAS LAS APPS INSTALADAS${NC}"
        show_status
        ;;
    status)
        show_status
        ;;
    *)
        echo "Uso: bash install_apps.sh [app|all|status]"
        echo ""
        echo "Apps disponibles:"
        echo "  moneyprinterturbo  - Videos Shorts/Reels automáticos"
        echo "  swarmui           - Frontend fácil para ComfyUI"
        echo "  comfyui-manager   - 1000+ workflows de comunidad"
        echo "  shortgpt          - Video largo → shorts"
        echo "  framepack         - Video de minutos (6GB VRAM)"
        echo "  bark              - TTS con emociones"
        echo ""
        echo "  all               - Instalar todo"
        echo "  status            - Ver estado"
        ;;
esac
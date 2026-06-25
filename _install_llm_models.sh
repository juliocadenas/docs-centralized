#!/bin/bash
# ============================================================
# AI Hub Madrid - Instalación de Modelos LLM Adicionales
# Servidor: NAB9 (100.105.27.27)
# GPU: RTX 5080 16GB VRAM
# ============================================================

set -e

echo "🧠 AI Hub Madrid - Instalando Modelos LLM Adicionales"
echo "======================================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Función para instalar un modelo
install_model() {
    local name=$1
    local tag=$2
    local size=$3
    local desc=$4
    
    echo -e "${CYAN}📦 Instalando ${name}...${NC}"
    echo -e "   Modelo: ${tag}"
    echo -e "   Tamaño: ${size}"
    echo -e "   Descripción: ${desc}"
    echo ""
    
    # Verificar si ya está instalado
    if ollama list 2>/dev/null | grep -q "${tag}"; then
        echo -e "${YELLOW}   ⚠️  ${tag} ya está instalado. Saltando...${NC}"
        echo ""
        return 0
    fi
    
    # Instalar
    ollama pull "${tag}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}   ✅ ${name} instalado correctamente${NC}"
    else
        echo -e "${RED}   ❌ Error instalando ${name}${NC}"
        return 1
    fi
    echo ""
}

# ============================================================
# MODELOS A INSTALAR
# ============================================================

echo -e "${YELLOW}VRAM disponible: 16GB RTX 5080${NC}"
echo -e "${YELLOW}Modelos a instalar:${NC}"
echo ""
echo "  1. qwen2.5:14b       - ~8GB  (Mejor calidad, razonamiento avanzado)"
echo "  2. llama3.2:3b       - ~2GB  (Ultra-rápido, tareas simples)"
echo "  3. gemma2:9b         - ~5.5GB (Alternativo de Google)"
echo ""
echo "  Total estimado en disco: ~15.5GB"
echo ""

read -p "¿Continuar con la instalación? (y/n): " confirm
if [[ $confirm != [yY] ]]; then
    echo "Instalación cancelada."
    exit 0
fi

echo ""
echo "=================================================="
echo ""

# Instalar modelos
install_model \
    "Qwen 2.5 14B" \
    "qwen2.5:14b" \
    "~8GB (Q4_K_M)" \
    "Modelo grande de alta calidad, mejor razonamiento y español"

install_model \
    "Llama 3.2 3B" \
    "llama3.2:3b" \
    "~2GB (Q4_K_M)" \
    "Ultra-rápido para tareas simples, ideal para clasificación y respuestas cortas"

install_model \
    "Gemma 2 9B" \
    "gemma2:9b" \
    "~5.5GB (Q4_K_M)" \
    "Modelo de Google, excelente calidad general"

# ============================================================
# VERIFICACIÓN
# ============================================================

echo "=================================================="
echo -e "${GREEN}✅ Instalación completada!${NC}"
echo ""
echo "Modelos disponibles en Ollama:"
echo ""
ollama list
echo ""

# Test rápido
echo "=================================================="
echo -e "${CYAN}🧪 Test rápido de modelos...${NC}"
echo ""

echo -e "${YELLOW}Test Qwen 2.5 14B:${NC}"
echo "¿Hola, en una frase, qué eres?" | ollama run qwen2.5:14b 2>/dev/null | head -3
echo ""

echo -e "${YELLOW}Test Llama 3.2 3B:${NC}"
echo "¿Hola, en una frase, qué eres?" | ollama run llama3.2:3b 2>/dev/null | head -3
echo ""

echo -e "${YELLOW}Test Gemma 2 9B:${NC}"
echo "¿Hola, en una frase, qué eres?" | ollama run gemma2:9b 2>/dev/null | head -3
echo ""

echo "=================================================="
echo -e "${GREEN}🎉 Todos los modelos instalados!${NC}"
echo ""
echo "Ahora puedes usarlos en:"
echo "  - AI Hub Studio: http://localhost:3000"
echo "  - API Gateway:   http://localhost:9000/v1/chat/completions"
echo ""
echo "Ejemplo API:"
echo '  curl -X POST http://localhost:9000/v1/chat/completions \'
echo '    -H "Content-Type: application/json" \'
echo '    -d "{\"model\":\"qwen2.5:14b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hola\"}]}"'
echo ""
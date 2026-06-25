#!/bin/bash
# ============================================================
# AI Hub Madrid - Instalación del Sistema RAG (Base de Conocimientos)
# Servidor: NAB9 (100.105.27.27)
# Requisitos: Ollama con nomic-embed-text ya instalado
# ============================================================

set -e

echo "🔍 AI Hub Madrid - Instalando Sistema RAG"
echo "==========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Verificar que nomic-embed-text está instalado
echo -e "${CYAN}1. Verificando nomic-embed-text...${NC}"
if ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
    echo -e "${GREEN}   ✅ nomic-embed-text ya está instalado${NC}"
else
    echo -e "${YELLOW}   ⚠️  nomic-embed-text no encontrado. Instalando...${NC}"
    ollama pull nomic-embed-text
    echo -e "${GREEN}   ✅ nomic-embed-text instalado${NC}"
fi
echo ""

# 2. Instalar dependencias de Python
echo -e "${CYAN}2. Instalando dependencias Python...${NC}"
echo -e "   - ChromaDB (vector database)"
echo -e "   - PyMuPDF (extracción de texto de PDFs)"
echo ""

pip install chromadb>=0.4.22 PyMuPDF>=1.24.0
echo -e "${GREEN}   ✅ Dependencias instaladas${NC}"
echo ""

# 3. Crear directorio para ChromaDB
echo -e "${CYAN}3. Creando almacenamiento para ChromaDB...${NC}"
mkdir -p /mnt/seagate/chromadb
echo -e "${GREEN}   ✅ Directorio creado: /mnt/seagate/chromadb${NC}"
echo ""

# 4. Reiniciar el Gateway para que cargue el nuevo router
echo -e "${CYAN}4. Reiniciando AI Hub Gateway...${NC}"
sudo systemctl restart ai-hub-gateway.service
sleep 3

if systemctl is-active --quiet ai-hub-gateway.service; then
    echo -e "${GREEN}   ✅ Gateway reiniciado correctamente${NC}"
else
    echo -e "${RED}   ❌ El Gateway no se reinició correctamente${NC}"
    echo -e "${YELLOW}   Revisa: sudo systemctl status ai-hub-gateway.service${NC}"
    exit 1
fi
echo ""

# 5. Verificar que el endpoint RAG responde
echo -e "${CYAN}5. Verificando endpoint RAG...${NC}"
sleep 2
RAG_HEALTH=$(curl -s http://localhost:9000/v1/rag/health)

if echo "$RAG_HEALTH" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}   ✅ RAG sistema operativo!${NC}"
    echo -e "   ${CYAN}$RAG_HEALTH${NC}"
else
    echo -e "${YELLOW}   ⚠️  Endpoint RAG responde pero ChromaDB puede no estar inicializado${NC}"
    echo -e "   Respuesta: $RAG_HEALTH"
fi
echo ""

# 6. Test rápido: crear colección de prueba
echo -e "${CYAN}6. Test rápido: creando colección de prueba...${NC}"
TEST_RESULT=$(curl -s -X POST http://localhost:9000/v1/rag/collections \
    -H "Content-Type: application/json" \
    -d '{"name":"test","description":"Colección de prueba"}')

if echo "$TEST_RESULT" | grep -q '"status":"created"'; then
    echo -e "${GREEN}   ✅ Colección 'test' creada correctamente${NC}"
    
    # Borrar la colección de prueba
    curl -s -X DELETE http://localhost:9000/v1/rag/collections/test > /dev/null
    echo -e "   Colección de prueba eliminada"
else
    echo -e "${YELLOW}   ⚠️  No se pudo crear colección de prueba${NC}"
    echo -e "   $TEST_RESULT"
fi
echo ""

# ============================================================
# RESUMEN
# ============================================================
echo "=========================================="
echo -e "${GREEN}✅ Sistema RAG instalado correctamente!${NC}"
echo "=========================================="
echo ""
echo "Endpoints disponibles:"
echo "  GET  /v1/rag/health              - Estado del sistema"
echo "  GET  /v1/rag/collections         - Listar colecciones"
echo "  POST /v1/rag/collections         - Crear colección"
echo "  POST /v1/rag/upload              - Subir documento"
echo "  POST /v1/rag/query               - Consultar base de conocimientos"
echo "  DELETE /v1/rag/collections/{name} - Eliminar colección"
echo ""
echo "Ejemplo de uso:"
echo '  # Subir un documento'
echo '  curl -X POST http://localhost:9000/v1/rag/upload \'
echo '    -F "file=@documento.pdf" \'
echo '    -F "collection=mi_proyecto"'
echo ""
echo '  # Consultar la base de conocimientos'
echo '  curl -X POST http://localhost:9000/v1/rag/query \'
echo '    -H "Content-Type: application/json" \'
echo '    -d "{\"query\":\"¿Qué dice el documento sobre X?\",\"collection\":\"mi_proyecto\"}"'
echo ""
echo "Almacenamiento: /mnt/seagate/chromadb/"
echo ""
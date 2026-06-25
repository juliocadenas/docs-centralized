# 🚀 Guía de Deploy v2.3 - AI Hub Madrid

## Resumen de mejoras implementadas (v2.1 → v2.3)

### Nuevos endpoints:
| Endpoint | Función |
|----------|---------|
| `POST /v1/video/agentic` | Pipeline video agentic completo (LLM→Flux→TTS→Remotion) |
| `POST /v1/rag/upload` | Subir documentos a base de conocimientos |
| `POST /v1/rag/query` | Consultar documentos con IA (RAG) |
| `GET /v1/rag/collections` | Listar colecciones |
| `POST /v1/rag/collections` | Crear colección |
| `DELETE /v1/rag/collections/{name}` | Eliminar colección |
| `GET /v1/rag/health` | Estado del sistema RAG |
| `POST /v1/embeddings` | Embeddings compatibles OpenAI |

### Nuevos modelos LLM:
- `qwen2.5:14b` - Alta calidad (~8GB)
- `gemma2:9b` - Google (~5.5GB)
- `llama3.2:3b` - Ultra-rápido (~2GB)

### Mejoras de infraestructura:
- ✅ GPU Manager optimizado (async subprocess, health check timeout)
- ✅ `mark_service_used` en embeddings/warm/vision
- ✅ Vision GPU lock para concurrencia
- ✅ OOM protection para Ollama y Gateway
- ✅ VRAM watchdog
- ✅ RAG con ChromaDB + PyMuPDF

---

## Cómo hacer el deploy en el NAB9

### Opción 1: Script automático (recomendado)

```bash
# En el NAB9 como root:
cd /mnt/seagate/repos/IA-HUB-MADRID1
git pull origin main
sudo bash _deploy_all.sh
```

### Opción 2: Deploy manual paso a paso

```bash
# 1. Git pull
cd /mnt/seagate/repos/IA-HUB-MADRID1
git pull origin main

# 2. Copiar archivos del Gateway
REPO=$(pwd)
GW=/mnt/seagate/api/ai-hub-gateway  # ajustar si está en otra ruta

cp $REPO/ai-hub-gateway/gateway/config.py $GW/gateway/
cp $REPO/ai-hub-gateway/main.py $GW/
cp $REPO/ai-hub-gateway/requirements.txt $GW/
cp $REPO/ai-hub-gateway/gateway/routers/*.py $GW/gateway/routers/
cp $REPO/ai-hub-gateway/gateway/services/*.py $GW/gateway/services/

# 3. Instalar dependencias RAG
pip3 install chromadb PyMuPDF

# 4. Instalar modelos LLM
ollama pull qwen2.5:14b
ollama pull gemma2:9b
ollama pull llama3.2:3b

# 5. Reiniciar Gateway
systemctl restart ai-hub-gateway

# 6. Verificar
sleep 5
curl http://localhost:9000/v1/rag/health
curl http://localhost:9000/  # debe decir version 2.3.0
```

---

## Verificar que todo funciona

```bash
# Gateway version
curl -s http://localhost:9000/ | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])"
# Debe decir: 2.3.0

# RAG health
curl -s http://localhost:9000/v1/rag/health | python3 -m json.tool
# Debe decir: {"status": "ok", ...}

# Modelos instalados
ollama list
# Debe mostrar: qwen2.5:7b, qwen2.5:14b, qwen2.5-coder:7b, gemma2:9b, llama3.1, llama3.2:3b, qwen2.5vl:7b, nomic-embed-text

# Test RAG
curl -X POST http://localhost:9000/v1/rag/collections \
  -H "Content-Type: application/json" \
  -d '{"name":"test", "description":"Colección de prueba"}'

# Test chat con nuevo modelo
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:14b","messages":[{"role":"user","content":"Hola"}]}'
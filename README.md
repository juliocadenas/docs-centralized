# 🚀 AI Hub Madrid - Centro de Creación con IA

> **Zero Tokens** — Todo corre en hardware propio (RTX 5080 16GB), sin APIs externas

## 📊 Estado Actual

| Componente | Versión NAB9 | Versión Código | Estado |
|-----------|--------------|----------------|--------|
| **Gateway** | v2.1.0 | **v2.3.0** | ⚠️ Pendiente deploy |
| **AI Hub Studio** | UI antigua | **UI nueva** | ⚠️ Pendiente deploy |
| **Modelos LLM** | 5 modelos | 8 modelos | ⚠️ Faltan 3 |
| **RAG System** | ❌ No instalado | ✅ Codeado | ⚠️ Pendiente |
| **Video Agentic** | ❌ No existe | ✅ Codeado | ⚠️ Pendiente |

## 🎯 Servicios Activos (6/15)

| Servicio | Puerto | VRAM | Estado |
|----------|--------|------|--------|
| Ollama LLM | 11434 | 4GB | ✅ Always-on |
| ComfyUI | 8188 | 2GB | ✅ Online |
| DocuMusic | 8000 | 4GB | ✅ Online |
| Wan2GP Video | 7860 | 8GB | ✅ Online |
| Piper TTS | 8010 | CPU | ✅ Always-on |
| Whisper STT | 8020 | 2GB | ✅ Always-on |

## 🌐 URLs

- **AI Hub Studio:** http://100.105.27.27:3000
- **Gateway API:** http://100.105.27.27:9000/v1
- **Swagger Docs:** http://100.105.27.27:9000/docs

## 📋 Para actualizar a v2.3.0

### Opción 1: Deploy automático (recomendado)

```bash
# En el NAB9 como root:
cd /mnt/seagate/repos/IA-HUB-MADRID1
git pull origin main
sudo bash DEPLOY_V23_NAB9.sh
```

### Opción 2: Test remoto desde Windows

```powershell
# Verifica qué endpoints funcionan sin tocar el NAB9
powershell -ExecutionPolicy Bypass -File TEST_REMOTE.ps1
```

## 🆕 Novedades v2.3.0

### Nuevos Endpoints
- `POST /v1/video/agentic` - Pipeline completo video (LLM→Flux→TTS→Remotion)
- `POST /v1/rag/upload` - Subir documentos a base de conocimientos
- `POST /v1/rag/query` - Consultar documentos con IA
- `POST /v1/embeddings` - Embeddings compatibles OpenAI
- `POST /v1/chat/vision` - Análisis de imágenes (Qwen 2.5-VL)

### Nuevos Modelos LLM
- `qwen2.5:14b` - Alta calidad (~8GB)
- `gemma2:9b` - Google (~5.5GB)
- `llama3.2:3b` - Ultra-rápido (~2GB)

### Nuevos Servicios
- **OmniVoice** (puerto 8030) - TTS en 646 idiomas
- **Remotion** (puerto 8601) - Render server para video agentic

## 🏗️ Arquitectura

```
Windows PC (desarrollo)
    ↓
NAB9 - Servidor GPU (100.105.27.27)
├── RTX 5080 16GB VRAM
├── 32GB RAM
├── AI Hub Gateway (FastAPI :9000)
├── AI Hub Studio (Next.js :3000)
├── Ollama, ComfyUI, DocuMusic, Wan2GP
├── Piper, Whisper, XTTS-v2, Fish Speech
├── Hallo2, LatentSync, LivePortrait, MuseTalk
└── Rembg, Real-ESRGAN, Higgsfield
    ↓
SERVIDOR01 - CPU tasks (100.83.253.87)
└── Scrapers, BDs, proyectos sin GPU
```

## 📚 Documentación

- [Gateway API](../docs-centralized/docs/ai-hub/gateway.md)
- [Servicios IA](../docs-centralized/docs/ai-hub/services.md)
- [Catálogo Modelos](../docs-centralized/docs/ai-hub/models.md)
- [Guía Deploy](DEPLOY_GUIDE.md)

## 🔧 Scripts Disponibles

| Script | Función |
|--------|---------|
| `DEPLOY_V23_NAB9.sh` | Deploy completo v2.1.0 → v2.3.0 en NAB9 |
| `TEST_REMOTE.ps1` | Test endpoints desde Windows (sin SSH) |
| `TEST_ENDPOINTS.sh` | Test endpoints en NAB9 |
| `_deploy_all.sh` | Deploy total (legacy) |
| `_install_llm_models.sh` | Instalar modelos LLM adicionales |
| `_install_openmontage.sh` | Instalar OpenMontage + Remotion |
| `_install_rag.sh` | Instalar sistema RAG |
| `_deploy_omnivoice.sh` | Deploy OmniVoice TTS |

---

**Regla de oro:** Zero tokens. Todo local. Compatible OpenAI. Docker-first.
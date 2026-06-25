"""
AI Hub Gateway - Main FastAPI Application.

A unified OpenAI-compatible API gateway that proxies to local AI services:
- Ollama (LLM)
- ComfyUI (Image Generation)
- DocuMusic (Audio/Music Generation)
- Wan2GP (Video Generation)

All services run locally on the Madrid server (RTX 5080 16GB).
Zero external API tokens required.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gateway.config import GATEWAY_VERSION, GATEWAY_PORT

# Allowed CORS origins - can be overridden via environment variable
ALLOWED_ORIGINS = os.environ.get(
    "GATEWAY_CORS_ORIGINS",
    "*"  # Default: allow all (local network only)
).split(",")
from gateway.gpu_manager import GPUManager
from gateway.routers import llm_router, images_router, audio_router, video_router, status_router, voice_router, avatar_router, effects_router
from gateway.routers.rag import router as rag_router
from gateway.routers.llm import set_service as set_llm_service
from gateway.routers.images import set_service as set_images_service
from gateway.routers.audio import set_service as set_audio_service
from gateway.routers.video import set_service as set_video_service
from gateway.routers.status import set_dependencies as set_status_deps
from gateway.services.ollama import OllamaService
from gateway.services.comfyui import ComfyUIService
from gateway.services.documusic import DocuMusicService
from gateway.services.wan2gp import Wan2GPService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize services
ollama_svc = OllamaService()
comfyui_svc = ComfyUIService()
documusic_svc = DocuMusicService()
wan2gp_svc = Wan2GPService()
gpu_mgr = GPUManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    logger.info(f"🚀 AI Hub Gateway v{GATEWAY_VERSION} starting...")
    logger.info(f"   Endpoint: http://0.0.0.0:{GATEWAY_PORT}/v1")

    # Inject services into routers
    set_llm_service(ollama_svc)
    set_images_service(comfyui_svc)
    set_audio_service(documusic_svc)
    set_video_service(wan2gp_svc)
    set_status_deps(gpu_mgr, ollama_svc)

    # Inject GPU manager into routers for VRAM tracking + GPU job semaphore
    from gateway.routers.images import set_gpu_manager as set_images_gpu
    from gateway.routers.audio import set_gpu_manager as set_audio_gpu
    from gateway.routers.video import set_gpu_manager as set_video_gpu
    from gateway.routers.avatar import set_gpu_manager as set_avatar_gpu
    set_images_gpu(gpu_mgr)
    set_audio_gpu(gpu_mgr)
    set_video_gpu(gpu_mgr)
    set_avatar_gpu(gpu_mgr)

    # Start auto-unload watchdog
    await gpu_mgr.start_watchdog()

    yield

    # Cleanup
    logger.info("🛑 Shutting down services...")
    await gpu_mgr.stop_watchdog()
    await ollama_svc.close()
    await comfyui_svc.close()
    await documusic_svc.close()
    await wan2gp_svc.close()
    logger.info("AI Hub Gateway stopped.")


# Create FastAPI app
app = FastAPI(
    title="AI Hub Madrid - Gateway API",
    description=(
        "Unified OpenAI-compatible API for all local AI services.\n\n"
        "## Supported Endpoints\n"
        "- `POST /v1/chat/completions` - LLM Chat (Ollama, supports vision + tools)\n"
        "- `POST /v1/chat/completions/stream` - Streaming LLM Chat (SSE)\n"
        "- `POST /v1/chat/vision` - Image Analysis (Qwen2.5-VL)\n"
        "- `POST /v1/embeddings` - Text Embeddings (nomic-embed-text)\n"
        "- `GET /v1/rag/health` - RAG System Health Check\n"
        "- `GET /v1/rag/collections` - List Knowledge Collections\n"
        "- `POST /v1/rag/collections` - Create Knowledge Collection\n"
        "- `POST /v1/rag/upload` - Upload Document to Knowledge Base\n"
        "- `POST /v1/rag/query` - Query Knowledge Base (RAG)\n"
        "- `DELETE /v1/rag/collections/{name}` - Delete Collection\n"
        "- `POST /v1/models/warm` - Pre-load Model into VRAM\n"
        "- `POST /v1/images/generations` - Image Generation (ComfyUI)\n"
        "- `POST /v1/audio/generations` - Audio/Music Generation (DocuMusic)\n"
        "- `POST /v1/audio/speech` - Text-to-Speech (Piper TTS)\n"
        "- `POST /v1/audio/transcriptions` - Speech-to-Text (Whisper STT)\n"
        "- `POST /v1/video/generations` - Video Generation (Wan2GP)\n"
        "- `POST /v1/video/agentic` - Full Agentic Video Pipeline (OpenMontage + Remotion)\n"
        "- `GET /v1/video/agentic/{job_id}/status` - Check Agentic Video Status\n"
        "- `POST /v1/avatar/lipsync` - Lip-sync (MuseTalk/LatentSync)\n"
        "- `POST /v1/avatar/portrait` - Portrait Animation (LivePortrait)\n"
        "- `POST /v1/avatar/digital-human` - Full Digital Human Pipeline\n"
        "- `POST /v1/effects/remove-bg` - Background Removal (Rembg)\n"
        "- `POST /v1/effects/upscale` - Image Upscale (Real-ESRGAN)\n"
        "- `GET /v1/models` - List All Models\n"
        "- `GET /v1/health` - Fast Health Check (for Docker/cron)\n"
        "- `GET /v1/status` - System Status\n"
        "- `GET /v1/infrastructure` - Infrastructure Map\n"
        "- `POST /v1/services/{name}/start` - Start Service\n"
        "- `POST /v1/services/{name}/stop` - Stop Service\n\n"
        "## Zero Tokens\n"
        "All models run locally. No external API calls. No tokens needed."
    ),
    version=GATEWAY_VERSION,
    lifespan=lifespan,
)

# CORS - Allow all origins for local network use
# NOTE: allow_credentials=False is intentional when allow_origins=["*"].
#       Browsers reject credentials with wildcard origins. If you need
#       credentials (cookies), set GATEWAY_CORS_ORIGINS to specific origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=(ALLOWED_ORIGINS != ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /v1 prefix (OpenAI-compatible)
app.include_router(llm_router, prefix="/v1", tags=["LLM (Chat)"])
app.include_router(images_router, prefix="/v1", tags=["Images"])
app.include_router(audio_router, prefix="/v1", tags=["Audio"])
app.include_router(video_router, prefix="/v1", tags=["Video"])
app.include_router(status_router, prefix="/v1", tags=["System"])
app.include_router(voice_router, prefix="/v1", tags=["Voice (TTS/STT)"])
app.include_router(avatar_router, prefix="/v1", tags=["Avatar & Digital Human"])
app.include_router(effects_router, prefix="/v1", tags=["Effects"])
app.include_router(rag_router, tags=["RAG"])


@app.get("/")
async def root():
    """Root endpoint with API overview."""
    return {
        "name": "AI Hub Madrid - Gateway",
        "version": GATEWAY_VERSION,
        "description": "Unified OpenAI-compatible API for local AI services",
        "docs": "/docs",
        "endpoint": "/v1",
        "zero_tokens": True,
    }


if __name__ == "__main__":
    import uvicorn
    # reload only in development; default to False for stability in production
    DEV_MODE = os.environ.get("GATEWAY_DEV", "0") == "1"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=GATEWAY_PORT,
        reload=DEV_MODE,
        log_level="info",
    )

"""
Status Router - System status, models list, service management, and infrastructure info.
"""
import logging
import time
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException

from ..config import (
    GATEWAY_VERSION,
    GPU_TOTAL_VRAM_MB,
    SERVER_HOSTNAME,
    SERVER_LAN_IP,
    SERVER_TAILSCALE_IP,
    SERVICES,
)
from ..gpu_manager import GPUManager
from ..models.schemas import ModelInfo, ModelList
from ..services.ollama import OllamaService

logger = logging.getLogger(__name__)
router = APIRouter()

gpu_manager: GPUManager = None
ollama_service: OllamaService = None
start_time: float = time.time()


def set_dependencies(gpu_mgr: GPUManager, ollama_svc: OllamaService):
    global gpu_manager, ollama_service
    gpu_manager = gpu_mgr
    ollama_service = ollama_svc


@router.get("/status")
async def get_status():
    """Get system status including all services and GPU info."""
    services_status = await gpu_manager.get_all_services_status()
    gpu_info = await gpu_manager.get_gpu_info()

    uptime = time.time() - start_time
    all_online = all(s["status"] == "online" for s in services_status if s["always_on"])

    return {
        "status": "ok" if all_online else "degraded",
        "gateway_version": GATEWAY_VERSION,
        "uptime_seconds": round(uptime, 1),
        "services": services_status,
        "gpu": gpu_info,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/models", response_model=ModelList)
async def list_models():
    """List all available models across all services (OpenAI-compatible)."""
    models = []

    # Get LLM models from Ollama
    if ollama_service:
        ollama_models = await ollama_service.list_models()
        for m in ollama_models:
            models.append(ModelInfo(**m))

    # Add static model entries from other services
    static_models = [
        # Image models
        ModelInfo(id="sdxl", type="text-to-image", service="comfyui", vram_mb=6144, status="available"),
        ModelInfo(id="flux", type="text-to-image", service="comfyui", vram_mb=8192, status="available"),
        ModelInfo(id="sd15", type="text-to-image", service="comfyui", vram_mb=2048, status="available"),
        # Audio models
        ModelInfo(id="yue", type="text-to-music", service="documusic", vram_mb=8192, status="available"),
        ModelInfo(id="ace-step", type="text-to-music", service="documusic", vram_mb=4096, status="available"),
        ModelInfo(id="diffrhythm", type="text-to-music", service="documusic", vram_mb=4096, status="available"),
        # Video models
        ModelInfo(id="wan2.1", type="text-to-video", service="wan2gp", vram_mb=6144, status="available"),
        ModelInfo(id="ltx-video", type="text-to-video", service="wan2gp", vram_mb=6144, status="available"),
        ModelInfo(id="hunyuan", type="text-to-video", service="comfyui", vram_mb=12288, status="available"),
        # TTS models
        ModelInfo(id="piper", type="text-to-speech", service="piper_tts", vram_mb=0, status="available"),
        ModelInfo(id="xtts-v2", type="text-to-speech", service="xtts_v2", vram_mb=3000, status="available"),
        # STT models
        ModelInfo(id="whisper", type="speech-to-text", service="whisper_stt", vram_mb=2000, status="available"),
    ]
    models.extend(static_models)

    return ModelList(data=models)


@router.get("/infrastructure")
async def get_infrastructure():
    """Get full infrastructure map in real-time (machine-readable version of INFRASTRUCTURE_MAP.md)."""
    services_status = await gpu_manager.get_all_services_status()
    gpu_info = await gpu_manager.get_gpu_info()

    return {
        "gateway": {
            "version": GATEWAY_VERSION,
            "status": "ok",
            "uptime_seconds": round(time.time() - start_time, 1),
            "endpoint": f"http://{SERVER_TAILSCALE_IP}:9000/v1",
        },
        "server": {
            "hostname": SERVER_HOSTNAME,
            "tailscale_ip": SERVER_TAILSCALE_IP,
            "lan_ip": SERVER_LAN_IP,
            "hardware": "RTX 5080 16GB VRAM + 32GB RAM",
            "os": "Pop!_OS 22.04 LTS",
        },
        "services": services_status,
        "gpu": gpu_info,
        "storage": {
            "ai_hub": "/mnt/seagate/ (1.8TB USB 3)",
            "models_canonical": "/mnt/seagate/models/",
            "models_links": "/mnt/seagate/links/",
            "output": "/mnt/seagate/output/",
        },
        "network": {
            "tailscale_ip": SERVER_TAILSCALE_IP,
            "lan_ip": SERVER_LAN_IP,
            "gateway_port": 9000,
        },
        "models_count": len(await _get_all_model_ids()),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/services/{service_name}/start")
async def start_service(service_name: str):
    """Start a service (may stop other services if VRAM is insufficient)."""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")
    result = await gpu_manager.start_service(service_name)
    if "error" in result:
        raise HTTPException(status_code=409, detail=result)
    return result


@router.post("/services/{service_name}/stop")
async def stop_service(service_name: str):
    """Stop a service to free VRAM."""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")
    result = await gpu_manager.stop_service(service_name)
    if "error" in result:
        raise HTTPException(status_code=409, detail=result)
    return result


async def _get_all_model_ids() -> list:
    """Helper to count all models."""
    models = []
    if ollama_service:
        ollama_models = await ollama_service.list_models()
        models.extend(ollama_models)
    models.extend(["yue", "ace-step", "diffrhythm", "wan2.1", "ltx-video", "hunyuan", "sd15"])
    return models
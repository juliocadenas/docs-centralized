"""
Images Router - OpenAI-compatible image generation endpoint.
Proxies to ComfyUI service.
"""
import logging

from fastapi import APIRouter, HTTPException

from ..models.schemas import ImageGenerationRequest, ImageGenerationResponse
from ..services.comfyui import ComfyUIService

logger = logging.getLogger(__name__)
router = APIRouter()

comfyui_service: ComfyUIService = None
gpu_manager = None


def set_service(service: ComfyUIService):
    global comfyui_service
    comfyui_service = service


def set_gpu_manager(gpu_mgr):
    global gpu_manager
    gpu_manager = gpu_mgr


@router.post("/images/generations")
async def create_image(request: ImageGenerationRequest):
    """
    Generate an image (OpenAI-compatible format with extensions).
    
    Supports all standard OpenAI parameters plus ComfyUI-specific ones
    (steps, cfg_scale, sampler, scheduler, negative_prompt).
    """
    if not comfyui_service:
        raise HTTPException(status_code=503, detail="Image service not initialized")

    # Mark service as used (resets idle timer)
    if gpu_manager:
        await gpu_manager.start_service("comfyui")  # Ensures it's running, starts if needed
        gpu_manager.mark_service_used("comfyui")
        # Acquire GPU lock - prevents OOM from concurrent GPU jobs
        await gpu_manager.acquire_gpu()
    try:
        # Parse size string (e.g., "1024x1024")
        width, height = 1024, 1024
        if request.size and "x" in request.size:
            parts = request.size.split("x")
            width, height = int(parts[0]), int(parts[1])

        result = await comfyui_service.generate_image(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt or "",
            width=width,
            height=height,
            steps=request.steps or 20,
            cfg_scale=request.cfg_scale or 7.0,
            seed=request.seed or -1,
            sampler=request.sampler or "euler",
            scheduler=request.scheduler or "normal",
            model=request.model or "sd15",
        )
    finally:
        if gpu_manager:
            await gpu_manager.release_gpu()

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result


@router.get("/images/status/{prompt_id}")
async def get_image_status(prompt_id: str):
    """Check the status of an image generation job."""
    if not comfyui_service:
        raise HTTPException(status_code=503, detail="Image service not initialized")

    result = await comfyui_service.get_prompt_status(prompt_id)
    return result
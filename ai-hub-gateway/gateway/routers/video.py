"""
Video Router - Video generation endpoint.
Proxies to Wan2GP service.
"""
import logging

from fastapi import APIRouter, HTTPException

from ..models.schemas import VideoGenerationRequest, VideoGenerationResponse
from ..services.wan2gp import Wan2GPService

logger = logging.getLogger(__name__)
router = APIRouter()

wan2gp_service: Wan2GPService = None
gpu_manager = None


def set_service(service: Wan2GPService):
    global wan2gp_service
    wan2gp_service = service


def set_gpu_manager(gpu_mgr):
    global gpu_manager
    gpu_manager = gpu_mgr


@router.post("/video/generations")
async def create_video(request: VideoGenerationRequest):
    """
    Generate a video from text prompt.
    
    Supports models: wan2.1, ltx-video, hunyuan.
    Configurable resolution, frames, steps, and sampling parameters.
    """
    if not wan2gp_service:
        raise HTTPException(status_code=503, detail="Video service not initialized")

    # Ensure service is running and mark as used
    if gpu_manager:
        await gpu_manager.start_service("wan2gp")
        gpu_manager.mark_service_used("wan2gp")
        # Acquire GPU lock - prevents OOM from concurrent GPU jobs
        await gpu_manager.acquire_gpu()
    try:
        result = await wan2gp_service.generate_video(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt or "",
            model=request.model or "wan2.1",
            width=request.width or 832,
            height=request.height or 480,
            frames=request.frames or 81,
            steps=request.steps or 20,
            cfg_scale=request.cfg_scale or 6.0,
            seed=request.seed or -1,
            sampler=request.sampler,
            scheduler=request.scheduler,
        )
    finally:
        if gpu_manager:
            await gpu_manager.release_gpu()

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result
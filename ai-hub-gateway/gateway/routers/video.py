"""
Video Router - Video generation endpoint.
Proxies to Wan2GP service.
"""
import logging
import httpx

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
    gpu_acquired = False
    if gpu_manager:
        try:
            await gpu_manager.start_service("wan2gp")
            gpu_manager.mark_service_used("wan2gp")
            # Acquire GPU lock - prevents OOM from concurrent GPU jobs
            await gpu_manager.acquire_gpu()
            gpu_acquired = True
        except Exception as e:
            logger.error(f"Failed to acquire GPU for video: {e}")
            raise HTTPException(status_code=503, detail=f"GPU unavailable: {str(e)}")

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
    except httpx.TimeoutException:
        logger.error("Wan2GP timeout generating video")
        raise HTTPException(status_code=504, detail="Video generation timed out. Try fewer frames or steps.")
    except httpx.ConnectError:
        logger.error("Cannot connect to Wan2GP service")
        raise HTTPException(status_code=502, detail="Wan2GP service is not responding. It may be loading models.")
    except Exception as e:
        logger.error(f"Unexpected error in video generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
    finally:
        if gpu_manager and gpu_acquired:
            await gpu_manager.release_gpu()

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result
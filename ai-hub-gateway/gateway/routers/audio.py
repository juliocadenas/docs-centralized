"""
Audio Router - Audio/music generation endpoint.
Proxies to DocuMusic service.
"""
import logging
import httpx

from fastapi import APIRouter, HTTPException

from ..models.schemas import AudioGenerationRequest, AudioGenerationResponse
from ..services.documusic import DocuMusicService

logger = logging.getLogger(__name__)
router = APIRouter()

documusic_service: DocuMusicService = None
gpu_manager = None


def set_service(service: DocuMusicService):
    global documusic_service
    documusic_service = service


def set_gpu_manager(gpu_mgr):
    global gpu_manager
    gpu_manager = gpu_mgr


@router.post("/audio/generations")
async def create_audio(request: AudioGenerationRequest):
    """
    Generate audio/music.
    
    Supports multiple models: yue, ace-step, diffrhythm.
    Accepts prompt, lyrics, tags, and generation parameters.
    """
    if not documusic_service:
        raise HTTPException(status_code=503, detail="Audio service not initialized")

    # Ensure service is running and mark as used
    gpu_acquired = False
    if gpu_manager:
        try:
            await gpu_manager.start_service("documusic")
            gpu_manager.mark_service_used("documusic")
            # Acquire GPU lock - prevents OOM from concurrent GPU jobs
            await gpu_manager.acquire_gpu()
            gpu_acquired = True
        except Exception as e:
            logger.error(f"Failed to acquire GPU for audio: {e}")
            raise HTTPException(status_code=503, detail=f"GPU unavailable: {str(e)}")
    try:
        result = await documusic_service.generate_audio(
            model=request.model or "ace-step",
            prompt=request.prompt,
            lyrics=request.lyrics,
            tags=request.tags or "",
            duration_seconds=request.duration_seconds if request.duration_seconds is not None else 30,
            seed=request.seed if request.seed is not None else -1,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
        )
    except httpx.TimeoutException:
        logger.error("DocuMusic timeout generating audio")
        raise HTTPException(status_code=504, detail="Audio generation timed out. Try a shorter duration.")
    except httpx.ConnectError:
        logger.error("Cannot connect to DocuMusic service")
        raise HTTPException(status_code=502, detail="DocuMusic service is not responding. It may be loading models.")
    except Exception as e:
        logger.error(f"Unexpected error in audio generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
    finally:
        if gpu_manager and gpu_acquired:
            await gpu_manager.release_gpu()

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result


@router.get("/audio/status/{job_id}")
async def get_audio_status(job_id: str):
    """Check the status of an audio generation job."""
    if not documusic_service:
        raise HTTPException(status_code=503, detail="Audio service not initialized")
    try:
        result = await documusic_service.get_status(job_id)
    except Exception as e:
        logger.error(f"Error checking audio status {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Failed to check job status: {str(e)}")
    return result

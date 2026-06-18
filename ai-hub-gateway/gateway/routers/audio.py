"""
Audio Router - Audio/music generation endpoint.
Proxies to DocuMusic service.
"""
import logging

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
    if gpu_manager:
        await gpu_manager.start_service("documusic")
        gpu_manager.mark_service_used("documusic")
        # Acquire GPU lock - prevents OOM from concurrent GPU jobs
        await gpu_manager.acquire_gpu()
    try:
        result = await documusic_service.generate_audio(
            model=request.model or "ace-step",
            prompt=request.prompt,
            lyrics=request.lyrics,
            tags=request.tags or "",
            duration_seconds=request.duration_seconds or 30,
            seed=request.seed or -1,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
        )
    finally:
        if gpu_manager:
            gpu_manager.release_gpu()

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result


@router.get("/audio/status/{job_id}")
async def get_audio_status(job_id: str):
    """Check the status of an audio generation job."""
    if not documusic_service:
        raise HTTPException(status_code=503, detail="Audio service not initialized")
    result = await documusic_service.get_status(job_id)
    return result
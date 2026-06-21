"""
Avatar Router - Lip-sync, portrait animation, and digital human pipeline.
Proxies to MuseTalk (:8041), LatentSync (:8043), LivePortrait (:8044), Hallo2 (:8070).
Also orchestrates the Digital Human pipeline: LLM -> TTS -> Lip-sync -> Video.
"""
import logging
import time
import uuid
import httpx
import asyncio

from fastapi import APIRouter, HTTPException
from typing import Optional

from ..models.schemas import (
    LipSyncRequest, LipSyncResponse,
    PortraitAnimationRequest, PortraitAnimationResponse,
    DigitalHumanRequest, DigitalHumanResponse,
)
from ..config import (
    MUSETALK_URL, LATENTSYNC_URL, LIVEPORTRAIT_URL, HALLO2_URL,
    PIPER_TTS_URL, OLLAMA_BASE_URL, SERVER_TAILSCALE_IP,
)

logger = logging.getLogger(__name__)
router = APIRouter()

gpu_manager = None


def set_gpu_manager(gpu_mgr):
    global gpu_manager
    gpu_manager = gpu_mgr


@router.post("/avatar/lipsync", response_model=LipSyncResponse)
async def create_lipsync(request: LipSyncRequest):
    """Create lip-sync video from input video/photo + audio."""
    task_id = str(uuid.uuid4())[:8]
    created = int(time.time())

    service_url = MUSETALK_URL if request.model == "musetalk" else LATENTSYNC_URL

    # Acquire GPU lock - prevents OOM from concurrent GPU jobs
    gpu_acquired = False
    if gpu_manager:
        try:
            await gpu_manager.acquire_gpu()
            gpu_acquired = True
        except Exception as e:
            logger.error(f"Failed to acquire GPU for lipsync: {e}")
            return LipSyncResponse(
                id=task_id, created=created, model=request.model,
                status="error: GPU unavailable"
            )
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{service_url}/run/predict",
                json={
                    "fn_index": 0,
                    "data": [
                        request.video_url,
                        request.audio_url,
                        request.fps,
                        request.batch_size,
                    ],
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                video_path = data.get("data", [None])[0]
                video_url = f"http://{SERVER_TAILSCALE_IP}:8041/file={video_path}" if video_path else None
                return LipSyncResponse(
                    id=task_id, created=created, model=request.model,
                    video_url=video_url, status="completed"
                )
            return LipSyncResponse(
                id=task_id, created=created, model=request.model,
                status="processing"
            )
    except httpx.ConnectError:
        logger.error("Lip-sync service not available")
        return LipSyncResponse(
            id=task_id, created=created, model=request.model,
            status=f"error: {request.model} service not available"
        )
    except Exception as e:
        logger.error(f"Lip-sync error: {e}")
        return LipSyncResponse(
            id=task_id, created=created, model=request.model,
            status=f"error: {str(e)}"
        )
    finally:
        if gpu_manager and gpu_acquired:
            await gpu_manager.release_gpu()


@router.post("/avatar/portrait", response_model=PortraitAnimationResponse)
async def create_portrait_animation(request: PortraitAnimationRequest):
    """Animate a portrait using LivePortrait."""
    task_id = str(uuid.uuid4())[:8]
    created = int(time.time())

    # Acquire GPU lock - prevents OOM from concurrent GPU jobs
    gpu_acquired = False
    if gpu_manager:
        try:
            await gpu_manager.acquire_gpu()
            gpu_acquired = True
        except Exception as e:
            logger.error(f"Failed to acquire GPU for portrait: {e}")
            return PortraitAnimationResponse(
                id=task_id, created=created,
                status="error: GPU unavailable"
            )
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{LIVEPORTRAIT_URL}/run/predict",
                json={
                    "fn_index": 0,
                    "data": [
                        request.source_image_url,
                        request.driving_video_url,
                        request.relative_motion,
                    ],
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                video_path = data.get("data", [None])[0]
                video_url = f"http://{SERVER_TAILSCALE_IP}:8044/file={video_path}" if video_path else None
                return PortraitAnimationResponse(
                    id=task_id, created=created,
                    video_url=video_url, status="completed"
                )
            return PortraitAnimationResponse(
                id=task_id, created=created, status="processing"
            )
    except httpx.ConnectError:
        return PortraitAnimationResponse(
            id=task_id, created=created,
            status="error: LivePortrait service not available (port 8044)"
        )
    except Exception as e:
        logger.error(f"Portrait animation error: {e}")
        return PortraitAnimationResponse(
            id=task_id, created=created, status=f"error: {str(e)}"
        )
    finally:
        if gpu_manager and gpu_acquired:
            await gpu_manager.release_gpu()


@router.post("/avatar/digital-human", response_model=DigitalHumanResponse)
async def create_digital_human(request: DigitalHumanRequest):
    """
    Full Digital Human Pipeline:
    1. (Optional) LLM generates script from prompt
    2. TTS converts script to audio
    3. Lip-sync creates talking video from avatar photo + audio

    This is the local equivalent of HeyGen Pro - zero tokens!
    """
    task_id = str(uuid.uuid4())[:8]
    created = int(time.time())
    steps = []

    # ── Step 1: Generate script with LLM (or use prompt directly) ──
    if request.use_llm:
        steps.append("llm_generation")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                llm_resp = await client.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": request.llm_model,
                        "messages": [
                            {"role": "system", "content": f"Eres un presentador natural. Genera un texto corto y natural para decir en voz alta basado en la instrucción del usuario. Responde SOLO con el texto a decir, en {request.tts_language}."},
                            {"role": "user", "content": request.prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.7, "num_predict": 200},
                    }
                )
                llm_data = llm_resp.json()
                script = llm_data.get("message", {}).get("content", request.prompt)
        except Exception as e:
            logger.warning(f"LLM step failed, using raw prompt: {e}")
            script = request.prompt
    else:
        script = request.prompt
        steps.append("llm_skipped")

    # ── Step 2: TTS - Convert script to audio ──
    steps.append("tts_generation")
    audio_url = None
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            tts_resp = await client.post(
                f"{PIPER_TTS_URL}/tts",
                json={
                    "text": script,
                    "voice": request.tts_voice,
                    "language": request.tts_language,
                }
            )
            if tts_resp.status_code == 200:
                # Piper returns audio bytes or URL
                content_type = tts_resp.headers.get("content-type", "")
                if "audio" in content_type:
                    # Save audio and return URL
                    audio_url = f"http://{SERVER_TAILSCALE_IP}:8010/tts_output/{task_id}.wav"
                elif "application/json" in content_type:
                    audio_url = tts_resp.json().get("audio_url")
    except Exception as e:
        logger.error(f"TTS step failed: {e}")
        return DigitalHumanResponse(
            id=task_id, created=created, status=f"error_tts: {str(e)}",
            script=script, pipeline_steps=steps
        )

    # ── Step 3: Lip-sync - Create talking video ──
    steps.append("lipsync_generation")
    video_url = None
    lipsync_service = MUSETALK_URL if request.lipsync_model == "musetalk" else LATENTSYNC_URL

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            lipsync_resp = await client.post(
                f"{lipsync_service}/run/predict",
                json={
                    "fn_index": 0,
                    "data": [
                        request.avatar_image_url,
                        audio_url,
                        request.fps,
                    ],
                }
            )
            if lipsync_resp.status_code == 200:
                data = lipsync_resp.json()
                video_path = data.get("data", [None])[0]
                port = 8041 if request.lipsync_model == "musetalk" else 8043
                video_url = f"http://{SERVER_TAILSCALE_IP}:{port}/file={video_path}" if video_path else None
    except Exception as e:
        logger.error(f"Lip-sync step failed: {e}")
        return DigitalHumanResponse(
            id=task_id, created=created, status=f"error_lipsync: {str(e)}",
            script=script, audio_url=audio_url, pipeline_steps=steps
        )

    return DigitalHumanResponse(
        id=task_id, created=created, status="completed",
        script=script, audio_url=audio_url, video_url=video_url,
        pipeline_steps=steps
    )
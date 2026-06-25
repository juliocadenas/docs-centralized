"""
Voice Router - TTS and STT endpoints.
Supports multiple TTS engines: Piper TTS, XTTS-v2, Fish Speech.
Proxies to Whisper STT (:8020).
OpenAI-compatible: /v1/audio/speech and /v1/audio/transcriptions
"""
import logging
import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from typing import Optional

from ..models.schemas import SpeechRequest, TranscriptionResponse

from ..config import PIPER_TTS_URL, XTTS_V2_URL, FISH_SPEECH_URL, WHISPER_STT_URL, OMNIVOICE_URL

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/audio/speech")
async def create_speech(request: SpeechRequest):
    """
    Generate speech from text (TTS).
    Supports multiple engines via model param:
    - 'piper' (default, CPU, fast)
    - 'xtts' (XTTS-v2, GPU, voice cloning)
    - 'fish' (Fish Speech, GPU, natural voice)

    Routes to the appropriate TTS engine based on model.
    """
    model = (request.model or "piper").lower()

    if model in ("xtts", "xtts-v2", "coqui"):
        return await _tts_xtts(request)
    elif model in ("fish", "fish-speech"):
        return await _tts_fish(request)
    elif model in ("omnivoice", "omni", "cosyvoice", "gpt-sovits", "voxcpm", "moss-tts"):
        return await _tts_omnivoice(request)
    else:
        # Default: Piper TTS
        return await _tts_piper(request)


async def _tts_piper(request: SpeechRequest):
    """Piper TTS - fast CPU-based TTS."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{PIPER_TTS_URL}/api/tts",
                data={
                    "text": request.input,
                    "voice": request.voice,
                    "language": request.language or "es",
                }
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Piper TTS error: {resp.text}")

            audio_data = resp.content
            media_type = "audio/wav"
            if request.response_format == "mp3":
                media_type = "audio/mpeg"

            return Response(content=audio_data, media_type=media_type)

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Piper TTS service not available (port 8010)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Piper TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _tts_xtts(request: SpeechRequest):
    """
    XTTS-v2 - multilingual TTS with voice cloning capability.
    Requires speaker_wav for voice cloning or uses default speaker.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "text": request.input,
                "language": request.language or "es",
                "speaker_wav": request.speaker_wav or "default",
                "temperature": 0.75,
            }
            resp = await client.post(
                f"{XTTS_V2_URL}/api/tts",
                json=payload,
            )
            if resp.status_code != 200:
                # Fallback to Piper if XTTS not available
                logger.warning(f"XTTS-v2 error {resp.status_code}, falling back to Piper")
                return await _tts_piper(request)

            audio_data = resp.content
            media_type = "audio/wav"
            if request.response_format == "mp3":
                media_type = "audio/mpeg"

            return Response(content=audio_data, media_type=media_type)

    except httpx.ConnectError:
        logger.warning("XTTS-v2 not available, falling back to Piper TTS")
        return await _tts_piper(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XTTS-v2 error: {e}, falling back to Piper")
        return await _tts_piper(request)


async def _tts_omnivoice(request: SpeechRequest):
    """
    OmniVoice Studio - 11 TTS engines, 646 languages, voice cloning.
    Best quality multilingual TTS. Includes: OmniVoice, Coqui, GPT-SoVITS, CosyVoice.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "text": request.input,
                "language": request.language or "es",
                "voice": request.voice or "default",
                "engine": (request.model or "omnivoice"),
            }
            resp = await client.post(
                f"{OMNIVOICE_URL}/api/tts",
                json=payload,
            )
            if resp.status_code != 200:
                logger.warning(f"OmniVoice error {resp.status_code}, falling back to Piper")
                return await _tts_piper(request)

            audio_data = resp.content
            media_type = "audio/wav"
            if request.response_format == "mp3":
                media_type = "audio/mpeg"

            return Response(content=audio_data, media_type=media_type)

    except httpx.ConnectError:
        logger.warning("OmniVoice not available, falling back to Piper TTS")
        return await _tts_piper(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OmniVoice error: {e}, falling back to Piper")
        return await _tts_piper(request)


async def _tts_fish(request: SpeechRequest):
    """
    Fish Speech - natural sounding TTS alternative.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "text": request.input,
                "language": request.language or "es",
                "voice": request.voice or "default",
            }
            resp = await client.post(
                f"{FISH_SPEECH_URL}/api/tts",
                json=payload,
            )
            if resp.status_code != 200:
                logger.warning(f"Fish Speech error {resp.status_code}, falling back to Piper")
                return await _tts_piper(request)

            audio_data = resp.content
            media_type = "audio/wav"
            if request.response_format == "mp3":
                media_type = "audio/mpeg"

            return Response(content=audio_data, media_type=media_type)

    except httpx.ConnectError:
        logger.warning("Fish Speech not available, falling back to Piper TTS")
        return await _tts_piper(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fish Speech error: {e}, falling back to Piper")
        return await _tts_piper(request)


@router.get("/audio/voices")
async def list_voices():
    """
    List available TTS voices across all engines.
    """
    voices = {"piper": [], "xtts": [], "fish": [], "omnivoice": []}

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Piper voices
        try:
            resp = await client.get(f"{PIPER_TTS_URL}/api/voices")
            if resp.status_code == 200:
                voices["piper"] = resp.json().get("voices", [])
        except Exception:
            pass

        # XTTS voices (when available)
        try:
            resp = await client.get(f"{XTTS_V2_URL}/api/voices")
            if resp.status_code == 200:
                voices["xtts"] = resp.json().get("voices", [])
        except Exception:
            pass

        # Fish Speech voices (when available)
        try:
            resp = await client.get(f"{FISH_SPEECH_URL}/api/voices")
            if resp.status_code == 200:
                voices["fish"] = resp.json().get("voices", [])
        except Exception:
            pass

        # OmniVoice voices (when available)
        try:
            resp = await client.get(f"{OMNIVOICE_URL}/api/voices")
            if resp.status_code == 200:
                voices["omnivoice"] = resp.json().get("voices", [])
        except Exception:
            pass

    return {
        "engines": ["piper", "xtts", "fish", "omnivoice"],
        "voices": voices,
    }


@router.post("/audio/transcriptions", response_model=TranscriptionResponse)
async def create_transcription(
    file: UploadFile = File(...),
    model: Optional[str] = Form("whisper-large-v3"),
    language: Optional[str] = Form("es"),
    prompt: Optional[str] = Form(None),
    response_format: Optional[str] = Form("json"),
    temperature: Optional[float] = Form(0.0),
):
    """Transcribe audio to text (STT). Proxies to Whisper STT on :8020."""
    try:
        audio_bytes = await file.read()
        files = {"audio": (file.filename or "audio.wav", audio_bytes, file.content_type or "audio/wav")}
        data = {"language": language or "es"}
        if prompt:
            data["prompt"] = prompt

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{WHISPER_STT_URL}/api/transcribe", files=files, data=data)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Whisper STT error: {resp.text}")

            result = resp.json()
            return TranscriptionResponse(
                text=result.get("text", ""),
                language=result.get("language", language),
                duration=result.get("duration"),
            )

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Whisper STT service not available (port 8020)")
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
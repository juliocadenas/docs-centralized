"""
Voice Router - TTS and STT endpoints.
Proxies to Piper TTS (:8010) and Whisper STT (:8020).
OpenAI-compatible: /v1/audio/speech and /v1/audio/transcriptions
"""
import logging
import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from typing import Optional

from ..models.schemas import SpeechRequest, TranscriptionResponse

logger = logging.getLogger(__name__)
router = APIRouter()

PIPER_TTS_URL = "http://localhost:8010"
WHISPER_STT_URL = "http://localhost:8020"


@router.post("/audio/speech")
async def create_speech(request: SpeechRequest):
    """Generate speech from text (TTS). Proxies to Piper TTS on :8010."""
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
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
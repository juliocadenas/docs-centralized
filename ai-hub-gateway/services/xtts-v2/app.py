"""
XTTS-v2 Service - Multilingual TTS with voice cloning
Uses Coqui TTS library.
"""
import os
import io
import tempfile
import logging
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="XTTS-v2 Service", version="1.0.0")

_tts = None


def get_tts():
    """Lazy load XTTS-v2 model."""
    global _tts
    if _tts is None:
        from TTS.api import TTS
        import torch
        logger.info("Cargando XTTS-v2...")
        _tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        if torch.cuda.is_available():
            _tts = _tts.to("cuda")
        logger.info("XTTS-v2 cargado!")
    return _tts


class TTSRequest(BaseModel):
    text: str
    language: str = "es"
    speaker_wav: Optional[str] = None  # Path to reference voice
    speaker: Optional[str] = "Ana Florence"  # Default speaker


@app.get("/")
async def health():
    return {"status": "ok", "service": "xtts-v2", "languages": ["es", "en", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko", "hi"]}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/tts")
async def tts(req: TTSRequest):
    """Convert text to speech with XTTS-v2."""
    try:
        model = get_tts()

        buf = io.BytesIO()
        if req.speaker_wav:
            # Voice cloning
            model.tts_to_file(
                text=req.text,
                language=req.language,
                speaker_wav=req.speaker_wav,
                file_path=buf,
            )
        else:
            # Default speaker
            model.tts_to_file(
                text=req.text,
                language=req.language,
                speaker=req.speaker,
                file_path=buf,
            )

        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/wav")
    except Exception as e:
        logger.error(f"XTTS error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/clone-voice")
async def clone_voice(
    text: str = "",
    language: str = "es",
    file: UploadFile = File(...),
):
    """Clone voice from uploaded sample and synthesize text."""
    try:
        # Save uploaded audio
        audio_bytes = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = get_tts()
        buf = io.BytesIO()
        model.tts_to_file(
            text=text,
            language=language,
            speaker_wav=tmp_path,
            file_path=buf,
        )
        os.unlink(tmp_path)

        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/wav")
    except Exception as e:
        logger.error(f"Voice clone error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
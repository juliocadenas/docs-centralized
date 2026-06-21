"""
Piper TTS Service - Fast Text-to-Speech on CPU
"""
import os
import io
import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Piper TTS Service", version="1.0.0")

# Voice models directory
VOICES_DIR = os.getenv("PIPER_VOICES", "/voices")
DEFAULT_VOICE = os.getenv("PIPER_VOICE", "es_ES-davefx-medium")

_voices = {}


def get_voice(voice_name: str):
    """Lazy load Piper voice model."""
    if voice_name not in _voices:
        from piper.voice import PiperVoice
        voice_path = os.path.join(VOICES_DIR, f"{voice_name}.onnx")
        if not os.path.exists(voice_path):
            # Fallback to default
            voice_path = os.path.join(VOICES_DIR, f"{DEFAULT_VOICE}.onnx")
        logger.info(f"Cargando voz Piper: {voice_path}")
        _voices[voice_name] = PiperVoice.load(voice_path)
    return _voices[voice_name]


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = DEFAULT_VOICE
    language: Optional[str] = "es"
    speaker_id: Optional[int] = 0
    speed: Optional[float] = 1.0


@app.get("/")
async def health():
    return {"status": "ok", "service": "piper-tts", "default_voice": DEFAULT_VOICE}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/voices")
async def list_voices():
    """List available voice models."""
    voices = []
    if os.path.exists(VOICES_DIR):
        for f in os.listdir(VOICES_DIR):
            if f.endswith(".onnx"):
                voices.append(f.replace(".onnx", ""))
    return {"voices": voices}


@app.post("/tts")
async def tts(req: TTSRequest):
    """Convert text to speech."""
    try:
        import wave
        voice = get_voice(req.voice)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            voice.synthesize_wav(req.text, wav_file, speaker_id=req.speaker_id,
                                 length_scale=1.0 / req.speed)

        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/wav")
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
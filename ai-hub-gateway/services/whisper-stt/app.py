"""
Whisper STT Service - Speech to Text API
Uses faster-whisper for GPU-accelerated transcription.
"""
import os
import tempfile
import logging
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper STT Service", version="1.0.0")

# Configuracion
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
WHISPER_COMPUTE = os.getenv("WHISPER_COMPUTE", "float16")

_model = None


def get_model():
    """Lazy load whisper model."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info(f"Cargando modelo Whisper {WHISPER_MODEL} en {WHISPER_DEVICE}...")
        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE,
            download_root="/models",
        )
        logger.info("Modelo cargado!")
    return _model


@app.get("/")
async def health():
    return {"status": "ok", "model": WHISPER_MODEL, "device": WHISPER_DEVICE}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Form("es"),
    prompt: Optional[str] = Form(None),
):
    """Transcribe audio file to text."""
    try:
        # Guardar audio temporal
        audio_bytes = await file.read()
        suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Transcribir
        model = get_model()
        segments, info = model.transcribe(
            tmp_path,
            language=language,
            initial_prompt=prompt,
            beam_size=5,
        )

        # Compilar texto
        text = " ".join([seg.text for seg in segments])

        # Limpiar
        os.unlink(tmp_path)

        return JSONResponse({
            "text": text.strip(),
            "language": info.language,
            "duration": round(info.duration, 2),
        })

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
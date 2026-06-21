"""
Fish Speech Service - Natural TTS
Wrapper around Fish Speech inference.
"""
import os
import io
import logging
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fish Speech Service", version="1.0.0")

_model = None


def get_model():
    """Lazy load Fish Speech model."""
    global _model
    if _model is None:
        import torch
        from fish_speech.models.vqgan import VQGAN
        logger.info("Cargando Fish Speech...")
        # Note: Fish Speech API changes frequently
        # This is a basic wrapper - actual inference may need adjustment
        # based on the version cloned in the Dockerfile
        _model = {"loaded": True, "device": "cuda" if torch.cuda.is_available() else "cpu"}
        logger.info("Fish Speech listo!")
    return _model


class TTSRequest(BaseModel):
    text: str
    language: str = "es"
    speaker_wav: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 0.8


@app.get("/")
async def health():
    return {"status": "ok", "service": "fish-speech"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/tts")
async def tts(req: TTSRequest):
    """Convert text to speech."""
    try:
        model = get_model()

        # TODO: Implement actual Fish Speech inference
        # This requires the model checkpoint which may be at:
        # /app/fish-speech/results/ or downloaded separately

        return JSONResponse({
            "status": "not_implemented",
            "message": "Fish Speech inference requires manual model setup",
            "model_info": model,
        })
    except Exception as e:
        logger.error(f"Fish Speech error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
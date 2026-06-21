"""
Rembg Service - Remove image background
Uses rembg with U2Net model.
"""
import io
import logging
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Rembg Service", version="1.0.0")


@app.get("/")
async def health():
    return {"status": "ok", "service": "rembg"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/remove")
async def remove_bg(
    file: UploadFile = File(...),
    model: str = "u2net",
    alpha_matting: bool = False,
):
    """Remove background from image."""
    try:
        from rembg import remove, new_session

        img_bytes = await file.read()

        # Create session with specified model
        session = new_session(model)

        output = remove(img_bytes, session=session, alpha_matting=alpha_matting)

        return StreamingResponse(
            io.BytesIO(output),
            media_type="image/png",
        )
    except Exception as e:
        logger.error(f"Rembg error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/remove-url")
async def remove_bg_url(req: dict):
    """Remove background from image URL."""
    try:
        import httpx
        from rembg import remove

        image_url = req.get("image_url")
        if not image_url:
            return JSONResponse({"error": "image_url required"}, status_code=400)

        async with httpx.AsyncClient() as client:
            resp = await client.get(image_url)
            img_bytes = resp.content

        output = remove(img_bytes)

        return StreamingResponse(
            io.BytesIO(output),
            media_type="image/png",
        )
    except Exception as e:
        logger.error(f"Rembg URL error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
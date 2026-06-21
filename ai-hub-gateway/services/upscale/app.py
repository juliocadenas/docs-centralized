"""
Upscale Service - Real-ESRGAN image upscaling API
"""
import io
import base64
import logging
import numpy as np
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Upscale Service (Real-ESRGAN)", version="1.0.0")

_upsampler = None


def get_upsampler():
    """Lazy load Real-ESRGAN model."""
    global _upsampler
    if _upsampler is None:
        import torch
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet

        # Real-ESRGAN x4plus architecture
        model = RRDBNet(
            num_in_ch=3, num_out_ch=3, num_feat=64,
            num_block=23, num_grow_ch=32, scale=4,
        )

        _upsampler = RealESRGANer(
            scale=4,
            model_path="RealESRGAN_x4plus.pth",
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=torch.cuda.is_available(),  # FP16 en GPU
        )
        logger.info("Real-ESRGAN cargado!")
    return _upsampler


@app.get("/")
async def health():
    return {"status": "ok", "service": "upscale", "model": "RealESRGAN_x4plus"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/upscale")
async def upscale(
    file: UploadFile = File(...),
    scale: int = Query(2, ge=1, le=4),
):
    """Upscale image using Real-ESRGAN."""
    try:
        # Leer imagen
        img_bytes = await file.read()
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        # Convertir a numpy
        img_np = np.array(img, dtype=np.uint8)

        # Upscale
        upsampler = get_upsampler()
        output, _ = upsampler.enhance(img_np, outscale=scale)

        # Convertir de vuelta a imagen
        out_img = Image.fromarray(output)

        # Codificar a base64
        buf = io.BytesIO()
        out_img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return JSONResponse({
            "status": "success",
            "image_base64": img_b64,
            "format": "png",
            "original_size": f"{img.width}x{img.height}",
            "output_size": f"{out_img.width}x{out_img.height}",
        })

    except Exception as e:
        logger.error(f"Upscale error: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
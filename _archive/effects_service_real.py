#!/usr/bin/env python3
"""
Effects Microservice - Rembg (background removal) + Real-ESRGAN (upscale)
Lightweight GPU services for the AI Hub Gateway.
Ports: 8050 (rembg), 8051 (upscale)
"""
import os
import io
import base64
import tempfile
import traceback
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Rembg Service (port 8050)
# ---------------------------------------------------------------------------
rembg_app = FastAPI(title="Rembg - Background Removal", version="1.0.0")

_rembg_session = None

def get_rembg_session():
    global _rembg_session
    if _rembg_session is None:
        from rembg import new_session
        _rembg_session = new_session("u2net")
    return _rembg_session


@rembg_app.get("/")
async def rembg_info():
    return {"service": "rembg", "status": "online", "port": 8050}


@rembg_app.get("/health")
async def rembg_health():
    return {"status": "healthy"}


@rembg_app.post("/remove")
async def remove_bg(image: UploadFile = File(...)):
    try:
        from rembg import remove
        input_bytes = await image.read()
        output_bytes = remove(input_bytes, session=get_rembg_session())
        return JSONResponse({
            "status": "success",
            "image_base64": base64.b64encode(output_bytes).decode(),
            "format": "png",
            "original_size": len(input_bytes),
            "output_size": len(output_bytes),
        })
    except ImportError:
        return JSONResponse(
            {"status": "error", "error": "rembg not installed. Run: pip install rembg[gpu]"},
            status_code=500,
        )
    except Exception as e:
        return JSONResponse(
            {"status": "error", "error": str(e), "trace": traceback.format_exc()[:500]},
            status_code=500,
        )


# ---------------------------------------------------------------------------
# Real-ESRGAN Service (port 8051)
# ---------------------------------------------------------------------------
esrgan_app = FastAPI(title="Real-ESRGAN - Upscale", version="1.0.0")

_esrgan_model = None

def get_esrgan_model():
    global _esrgan_model
    if _esrgan_model is None:
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet
        model_path = os.path.expanduser(
            os.environ.get("ESRGAN_MODEL", "~/.cache/realesrgan/RealESRGAN_x4plus.pth")
        )
        # x4plus model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        _esrgan_model = RealESRGANer(
            scale=4,
            model_path=model_path,
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=True,  # Use FP16 on GPU
            gpu_id=0,
        )
    return _esrgan_model


@esrgan_app.get("/")
async def esrgan_info():
    return {"service": "real-esrgan", "status": "online", "port": 8051}


@esrgan_app.get("/health")
async def esrgan_health():
    return {"status": "healthy"}


@esrgan_app.post("/upscale")
async def upscale_image(
    image: UploadFile = File(...),
    scale: int = Query(4, ge=2, le=8),
):
    try:
        import numpy as np
        import cv2
        from PIL import Image

        input_bytes = await image.read()

        # Convert bytes to numpy array
        img = Image.open(io.BytesIO(input_bytes))
        img_array = np.array(img)

        # Handle RGBA -> RGB
        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        elif len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)

        upsampler = get_esrgan_model()
        output, _ = upsampler.enhance(img_array, outscale=scale)

        # Convert back to PNG bytes
        output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        result_img = Image.fromarray(output_rgb)
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        output_bytes = buf.getvalue()

        return JSONResponse({
            "status": "success",
            "image_base64": base64.b64encode(output_bytes).decode(),
            "format": "png",
            "original_size": len(input_bytes),
            "output_size": len(output_bytes),
            "scale": scale,
            "dimensions": f"{output_rgb.shape[1]}x{output_rgb.shape[0]}",
        })
    except ImportError:
        return JSONResponse(
            {"status": "error", "error": "realesrgan not installed. Run: pip install realesrgan basicsr"},
            status_code=500,
        )
    except Exception as e:
        return JSONResponse(
            {"status": "error", "error": str(e), "trace": traceback.format_exc()[:500]},
            status_code=500,
        )


if __name__ == "__main__":
    import threading
    import uvicorn

    def run_rembg():
        uvicorn.run(rembg_app, host="0.0.0.0", port=8050, log_level="warning")

    def run_esrgan():
        uvicorn.run(esrgan_app, host="0.0.0.0", port=8051, log_level="warning")

    t1 = threading.Thread(target=run_rembg, daemon=True)
    t2 = threading.Thread(target=run_esrgan, daemon=True)
    t1.start()
    t2.start()
    t1.join()
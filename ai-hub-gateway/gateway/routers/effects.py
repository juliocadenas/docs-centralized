"""
Effects Router - Background removal, upscaling.
Proxies to Rembg (:8050) and Real-ESRGAN (:8051).
Backends return JSON with image_base64 field.
"""
import logging
import base64
import uuid
import httpx

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

REMBG_URL = "http://localhost:8050"
UPSCALE_URL = "http://localhost:8051"


async def _fetch_image(image_url: str) -> tuple[bytes, str]:
    """Download image from URL, return (bytes, content_type)."""
    headers = {"User-Agent": "AI-Hub-Gateway/2.0 (compatible; image-processor)"}
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        resp = await client.get(image_url, follow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/png")
        return resp.content, content_type


def _decode_image_response(resp: httpx.Response) -> Response:
    """Handle backend response - decode base64 if JSON, pass through if binary."""
    ct = resp.headers.get("content-type", "")
    
    if "json" in ct:
        # Backend returns JSON with image_base64
        data = resp.json()
        if data.get("status") == "success" and "image_base64" in data:
            img_bytes = base64.b64decode(data["image_base64"])
            fmt = data.get("format", "png")
            return Response(
                content=img_bytes,
                media_type=f"image/{fmt}",
                headers={"X-Original-Size": str(data.get("original_size", "")),
                         "X-Output-Size": str(data.get("output_size", ""))}
            )
        else:
            raise HTTPException(status_code=502, detail=f"Backend error: {data}")
    else:
        # Binary response
        return Response(content=resp.content, media_type=ct or "image/png")


@router.post("/effects/remove-bg")
async def remove_background(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    return_mask: Optional[bool] = Form(False),
):
    """Remove background from image using Rembg (:8050)."""
    task_id = str(uuid.uuid4())[:8]

    try:
        if file:
            img_bytes = await file.read()
            ct = file.content_type or "image/png"
        elif image_url:
            img_bytes, ct = await _fetch_image(image_url)
        else:
            raise HTTPException(status_code=422, detail="Provide 'file' (upload) or 'image_url'")

        files = {"image": ("image.png", img_bytes, ct)}
        data = {}
        if return_mask:
            data["return_mask"] = "true"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{REMBG_URL}/remove", files=files, data=data)
            if resp.status_code == 200:
                response = _decode_image_response(resp)
                response.headers["X-Task-Id"] = task_id
                return response
            raise HTTPException(status_code=502, detail=f"Rembg error: {resp.text[:200]}")

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Rembg service not available (port 8050)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Background removal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/effects/upscale")
async def upscale_image(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    scale: Optional[int] = Form(2),
):
    """Upscale image using Real-ESRGAN (:8051)."""
    task_id = str(uuid.uuid4())[:8]

    try:
        if file:
            img_bytes = await file.read()
            ct = file.content_type or "image/png"
        elif image_url:
            img_bytes, ct = await _fetch_image(image_url)
        else:
            raise HTTPException(status_code=422, detail="Provide 'file' (upload) or 'image_url'")

        files = {"image": ("image.png", img_bytes, ct)}

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{UPSCALE_URL}/upscale", files=files, params={"scale": scale})
            if resp.status_code == 200:
                response = _decode_image_response(resp)
                response.headers["X-Task-Id"] = task_id
                return response
            raise HTTPException(status_code=502, detail=f"Upscale error: {resp.text[:200]}")

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Upscale service not available (port 8051)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upscale error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
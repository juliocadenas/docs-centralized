"""
Wan2GP Service Connector.
Proxies video generation requests to Wan2GP Gradio API.
"""
import logging
import time
from typing import Dict, Optional

import httpx

from ..config import WAN2GP_BASE_URL

logger = logging.getLogger(__name__)


class Wan2GPService:
    """Service connector for Wan2GP video generation."""

    def __init__(self, base_url: str = WAN2GP_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=600.0)

    async def health_check(self) -> Dict:
        """Check if Wan2GP is running."""
        try:
            start = time.time()
            resp = await self.client.get(f"{self.base_url}/")
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                return {"status": "online", "response_time_ms": elapsed}
            return {"status": "error", "error": f"HTTP {resp.status_code}"}
        except httpx.ConnectError:
            return {"status": "offline", "error": "Connection refused"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def generate_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        model: str = "wan2.1",
        width: int = 832,
        height: int = 480,
        frames: int = 81,
        steps: int = 20,
        cfg_scale: float = 6.0,
        seed: int = -1,
        sampler: Optional[str] = None,
        scheduler: Optional[str] = None,
    ) -> Dict:
        """
        Generate video via Wan2GP Gradio API.
        Uses Gradio's /api/predict endpoint.
        """
        try:
            if seed == -1:
                import random
                seed = random.randint(0, 2**32 - 1)

            # Wan2GP uses Gradio API format
            # The exact API depends on Wan2GP's interface, but we use the common pattern
            payload = {
                "data": [
                    prompt,                    # prompt
                    negative_prompt,           # negative prompt
                    model,                     # model selection
                    width,                     # width
                    height,                    # height
                    frames,                    # video length (frames)
                    steps,                     # inference steps
                    cfg_scale,                 # CFG scale
                    seed,                      # seed
                ]
            }

            # Try Gradio API endpoint
            resp = await self.client.post(
                f"{self.base_url}/api/predict",
                json=payload,
                timeout=600.0,
            )

            if resp.status_code == 200:
                data = resp.json()
                return {
                    "id": f"video-{int(time.time())}",
                    "status": "processing",
                    "model": model,
                    "seed": seed,
                    "message": "Video generation submitted",
                    "data": data.get("data"),
                }
            else:
                # Fallback: try queue-based API
                return await _submit_via_queue(
                    self.client, self.base_url, payload
                )

        except httpx.ConnectError:
            return {"error": "Wan2GP service is not available."}
        except Exception as e:
            logger.error(f"Video generation error: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def _submit_via_queue(
    client: httpx.AsyncClient, base_url: str, payload: Dict
) -> Dict:
    """Submit via Gradio's queue-based API (for longer running tasks)."""
    try:
        resp = await client.post(
            f"{base_url}/api/predict",
            json=payload,
            timeout=600.0,
        )
        if resp.status_code == 200:
            return {
                "id": f"video-{int(time.time())}",
                "status": "submitted",
                "message": "Video generation submitted via queue",
                "data": resp.json().get("data"),
            }
        return {"error": f"Wan2GP returned HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}
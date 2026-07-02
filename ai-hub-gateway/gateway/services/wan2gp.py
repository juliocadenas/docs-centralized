"""
Wan2GP Service Connector.
Proxies video generation requests to Wan2GP Gradio API.
Supports both Gradio 3.x (direct) and Gradio 4.x (SSE queue) API formats.
"""
import logging
import time
import re
from typing import Dict, Optional, List

import httpx

from ..config import WAN2GP_BASE_URL

logger = logging.getLogger(__name__)


class Wan2GPService:
    """Service connector for Wan2GP video generation via Gradio API."""

    def __init__(self, base_url: str = WAN2GP_BASE_URL):
        self.base_url = base_url.rstrip("/")
        # Use separate clients: short timeout for health, long for generation
        self.client = httpx.AsyncClient(timeout=600.0)

    async def health_check(self) -> Dict:
        """Check if Wan2GP is running."""
        try:
            start = time.time()
            resp = await self.client.get(f"{self.base_url}/", timeout=10.0)
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
        Tries Gradio 4.x SSE format first, then falls back to Gradio 3.x direct format.
        Blocks until the video is ready (up to 10 minutes) and returns the URL.
        """
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        # Map duration/resolution to frames/size if needed
        # Wan2GP expects: prompt, negative_prompt, model, width, height, frames, steps, cfg, seed
        payload_data = [
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

        # ── STRATEGY 1: Try Gradio 4.x API (SSE-based) ──
        try:
            result = await self._generate_gradio_v4(payload_data)
            if result and "error" not in result:
                return result
            if result and "error" in result:
                logger.info(f"Gradio v4 failed: {result['error']}, trying v3...")
        except Exception as e:
            logger.info(f"Gradio v4 exception: {e}, trying v3...")

        # ── STRATEGY 2: Try Gradio 3.x API (direct response) ──
        try:
            result = await self._generate_gradio_v3(payload_data)
            if result and "error" not in result:
                return result
        except Exception as e:
            logger.error(f"Gradio v3 also failed: {e}")

        # ── STRATEGY 3: Try /api/predict with fn_index variations ──
        try:
            result = await self._generate_gradio_predict(payload_data)
            if result and "error" not in result:
                return result
        except Exception as e:
            logger.error(f"All Gradio strategies failed: {e}")

        return {"error": "Wan2GP service did not return a valid video. Check if the service is running."}

    async def _generate_gradio_v4(self, payload_data: List) -> Optional[Dict]:
        """
        Gradio 4.x API: POST to /gradio_api/call/predict → get event_id
        Then GET /gradio_api/call/predict/{event_id} → SSE stream with result
        """
        logger.info("Trying Gradio 4.x API format...")

        # Step 1: Submit the prediction
        resp = await self.client.post(
            f"{self.base_url}/gradio_api/call/predict",
            json={"data": payload_data},
            timeout=30.0,
        )

        if resp.status_code != 200:
            return {"error": f"Gradio v4 submit returned HTTP {resp.status_code}"}

        event_data = resp.json()
        event_id = event_data.get("event_id")
        if not event_id:
            return {"error": "No event_id in Gradio v4 response"}

        logger.info(f"Gradio v4 event_id: {event_id}, polling for result...")

        # Step 2: Poll SSE endpoint for the result
        # Gradio 4.x sends events: 'complete', 'generating', 'error'
        video_url = await self._poll_gradio_sse(event_id)
        if video_url:
            return {
                "id": f"video-{int(time.time())}",
                "created": int(time.time()),
                "model": payload_data[2] if len(payload_data) > 2 else "wan2.1",
                "video_url": video_url,
                "url": video_url,
                "status": "completed",
                "seed": payload_data[8] if len(payload_data) > 8 else -1,
            }

        return {"error": "Gradio v4 polling timed out without video result"}

    async def _poll_gradio_sse(self, event_id: str, timeout: int = 600) -> Optional[str]:
        """
        Poll the Gradio SSE endpoint until we get the video result.
        Returns the video URL or None if timed out.
        """
        import asyncio

        sse_url = f"{self.base_url}/gradio_api/call/predict/{event_id}"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Use streaming to read SSE events
                async with self.client.stream("GET", sse_url, timeout=30.0) as resp:
                    if resp.status_code != 200:
                        await asyncio.sleep(2)
                        continue

                    event_type = None
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                            import json
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            if event_type == "complete":
                                # data should be the output array
                                video_url = _extract_video_url(data, self.base_url)
                                if video_url:
                                    logger.info(f"Video ready: {video_url}")
                                    return video_url
                                logger.warning(f"Complete event but no video URL in: {data}")
                                return None

                            elif event_type == "error":
                                logger.error(f"Gradio SSE error: {data}")
                                return None

            except httpx.ReadTimeout:
                # Expected for SSE - keep polling
                continue
            except Exception as e:
                logger.debug(f"SSE poll error: {e}")
                await asyncio.sleep(2)

        logger.error("SSE polling timed out")
        return None

    async def _generate_gradio_v3(self, payload_data: List) -> Optional[Dict]:
        """
        Gradio 3.x API: POST to /api/predict → direct JSON response with result.
        May take a while (blocking until video is generated).
        """
        logger.info("Trying Gradio 3.x API format (blocking)...")

        resp = await self.client.post(
            f"{self.base_url}/api/predict",
            json={"data": payload_data, "fn_index": 0},
            timeout=600.0,
        )

        if resp.status_code != 200:
            return {"error": f"Gradio v3 returned HTTP {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        result_data = data.get("data", [])
        video_url = _extract_video_url(result_data, self.base_url)

        if video_url:
            return {
                "id": data.get("hash", f"video-{int(time.time())}"),
                "created": int(time.time()),
                "model": payload_data[2] if len(payload_data) > 2 else "wan2.1",
                "video_url": video_url,
                "url": video_url,
                "status": "completed",
                "seed": payload_data[8] if len(payload_data) > 8 else -1,
            }

        return {"error": "Gradio v3 returned no video URL in response data"}

    async def _generate_gradio_predict(self, payload_data: List) -> Optional[Dict]:
        """
        Fallback: Try various Gradio endpoint patterns.
        Some Wan2GP builds use /predict or /api/predict without fn_index.
        """
        logger.info("Trying fallback Gradio endpoint patterns...")

        # Try without fn_index
        for endpoint in ["/api/predict", "/predict", "/run/predict"]:
            try:
                resp = await self.client.post(
                    f"{self.base_url}{endpoint}",
                    json={"data": payload_data},
                    timeout=600.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result_data = data.get("data", [])
                    # Also check if the response itself contains the data
                    if not result_data and isinstance(data, list):
                        result_data = data

                    video_url = _extract_video_url(result_data, self.base_url)
                    if video_url:
                        return {
                            "id": f"video-{int(time.time())}",
                            "created": int(time.time()),
                            "model": payload_data[2] if len(payload_data) > 2 else "wan2.1",
                            "video_url": video_url,
                            "url": video_url,
                            "status": "completed",
                            "seed": payload_data[8] if len(payload_data) > 8 else -1,
                        }
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} failed: {e}")
                continue

        return {"error": "All Gradio endpoint patterns failed"}

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def _extract_video_url(data: any, base_url: str) -> Optional[str]:
    """
    Extract video URL from Gradio response data.
    Gradio returns video outputs in various formats:
    - {"path": "/tmp/.../video.mp4", "url": "...", "orig_name": "video.mp4"}
    - {"name": "video.mp4", "data": "base64...", "is_file": false}
    - Direct URL string
    - List of any of the above
    """
    if not data:
        return None

    # Handle list (Gradio returns data as array)
    if isinstance(data, list):
        for item in data:
            url = _extract_video_url(item, base_url)
            if url:
                return url
        return None

    # Handle string (could be a direct URL or file path)
    if isinstance(data, str):
        if data.startswith("http"):
            return data
        if data.endswith((".mp4", ".webm", ".avi", ".gif")):
            return _file_to_url(data, base_url)
        return None

    # Handle dict (Gradio file output)
    if isinstance(data, dict):
        # Direct URL field
        if "url" in data and data["url"]:
            url = data["url"]
            if url.startswith("http"):
                return url
            return _file_to_url(url, base_url)

        # Path field (Gradio 4.x style)
        if "path" in data and data["path"]:
            return _file_to_url(data["path"], base_url)

        # Name field with is_file
        if "name" in data and data.get("is_file"):
            return _file_to_url(data["name"], base_url)

        # orig_name with path
        if "path" in data and data.get("orig_name"):
            return _file_to_url(data["path"], base_url)

    return None


def _file_to_url(path: str, base_url: str) -> str:
    """
    Convert a file path from Gradio response to a URL.
    Gradio serves files at /file=<path> or /gradio_api/file=<path>
    """
    # Already a full URL
    if path.startswith("http"):
        return path

    # Remove any leading server path components
    # Gradio paths are usually absolute like /tmp/gradio/.../video.mp4
    path = path.replace("\\", "/")

    # Try Gradio 4.x format first
    return f"{base_url}/gradio_api/file={path}"
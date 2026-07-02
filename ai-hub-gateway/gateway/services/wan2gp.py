"""
Wan2GP Service Connector.
Interfaces with Wan2GP v11.84 (Gradio 5.29.0) via HTTP Gradio API.

Flow:
1. fill_wizard_prompt - sets the prompt
2. process_prompt_and_add_tasks - adds to generation queue
3. prepare_generate_video - starts generation
4. Poll _refresh_gallery for output video URL
"""
import logging
import time
import asyncio
import json
from typing import Dict, Optional, List

import httpx

from ..config import WAN2GP_BASE_URL

logger = logging.getLogger(__name__)

# Gradio 5.x API base for calls
GRADIO_CALL_PREFIX = "/gradio_api/call"


class Wan2GPService:
    """Service connector for Wan2GP video generation via Gradio 5.x HTTP API."""

    def __init__(self, base_url: str = WAN2GP_BASE_URL):
        self.base_url = base_url.rstrip("/")
        # Short timeout client for API calls
        self.client = httpx.AsyncClient(timeout=30.0)

    async def health_check(self) -> Dict:
        """Check if Wan2GP is running."""
        try:
            start = time.time()
            resp = await self.client.get(f"{self.base_url}/config", timeout=10.0)
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                # Check version
                data = resp.json()
                version = data.get("version", "unknown")
                return {
                    "status": "online",
                    "response_time_ms": elapsed,
                    "version": version,
                }
            return {"status": "error", "error": f"HTTP {resp.status_code}"}
        except httpx.ConnectError:
            return {"status": "offline", "error": "Connection refused"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _call_gradio_endpoint(
        self,
        endpoint: str,
        data: list,
        timeout: float = 30.0,
    ) -> Optional[tuple]:
        """
        Call a Gradio 5.x API endpoint and get result via SSE.

        Returns (event_id, result_data) tuple or None on failure.
        """
        url = f"{self.base_url}{GRADIO_CALL_PREFIX}/{endpoint.lstrip('/')}"

        try:
            # Step 1: Submit the call
            resp = await self.client.post(
                url,
                json={"data": data},
                timeout=timeout,
            )

            if resp.status_code != 200:
                logger.error(
                    f"Gradio call {endpoint} returned {resp.status_code}: {resp.text[:200]}"
                )
                return None

            event_data = resp.json()
            event_id = event_data.get("event_id")
            if not event_id:
                logger.error(f"No event_id from {endpoint}: {event_data}")
                return None

            logger.debug(f"{endpoint} submitted, event_id={event_id}")

            # Step 2: Get result via SSE
            sse_url = f"{url}/{event_id}"
            result = await self._read_sse(sse_url, timeout=timeout)

            return (event_id, result)

        except httpx.TimeoutException:
            logger.warning(f"{endpoint} timed out")
            return None
        except Exception as e:
            logger.error(f"{endpoint} failed: {e}")
            return None

    async def _read_sse(self, url: str, timeout: float = 30.0) -> Optional[list]:
        """Read SSE stream from Gradio result endpoint."""
        try:
            async with self.client.stream("GET", url, timeout=timeout) as resp:
                if resp.status_code != 200:
                    logger.warning(f"SSE returned {resp.status_code}")
                    return None

                event_type = None
                async for line in resp.aiter_lines():
                    line = line.strip()

                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:") and event_type:
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        if event_type == "complete":
                            return data
                        elif event_type == "error":
                            logger.error(f"Gradio SSE error: {data}")
                            return None
        except httpx.TimeoutException:
            logger.warning(f"SSE read timed out for {url}")
        except Exception as e:
            logger.error(f"SSE read failed: {e}")

        return None

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
        Generate video via Wan2GP.

        Uses Gradio 5.x HTTP API with the correct endpoint sequence.
        """
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        # Check service health
        health = await self.health_check()
        if health.get("status") != "online":
            return {
                "error": f"Wan2GP is {health.get('status')}: {health.get('error', '')}",
                "webui_url": self.base_url,
            }

        logger.info(f"Wan2GP: Starting generation for '{prompt[:60]}...'")

        # ── STEP 1: fill_wizard_prompt ──
        # Params: [wizard_prompt_activated, ???, wizard_prompt]
        logger.info("Wan2GP [1/3]: Setting prompt via fill_wizard_prompt...")
        result = await self._call_gradio_endpoint(
            "/fill_wizard_prompt",
            ["on", "", prompt],
            timeout=30.0,
        )
        if result is None:
            logger.warning("fill_wizard_prompt failed, trying to continue anyway")

        # ── STEP 2: process_prompt_and_add_tasks ──
        # Params: [wizard_prompt_activated_var, wizard_variables_names, wizard_prompt]
        logger.info("Wan2GP [2/3]: Adding task via process_prompt_and_add_tasks...")
        result = await self._call_gradio_endpoint(
            "/process_prompt_and_add_tasks",
            ["on", "", prompt],
            timeout=30.0,
        )
        if result is None:
            logger.error("process_prompt_and_add_tasks failed")
            return {
                "error": "Failed to add video task to Wan2GP queue",
                "webui_url": self.base_url,
            }

        # ── STEP 3: prepare_generate_video ──
        # No params
        logger.info("Wan2GP [3/3]: Starting generation via prepare_generate_video...")
        result = await self._call_gradio_endpoint(
            "/prepare_generate_video",
            [],
            timeout=60.0,
        )

        # ── STEP 4: Poll gallery for output video ──
        logger.info("Wan2GP: Generation started, polling gallery for output...")
        video_url = await self._poll_gallery_for_video(timeout=600)

        if video_url:
            logger.info(f"Wan2GP: Video ready at {video_url}")
            return {
                "id": f"video-{int(time.time())}",
                "created": int(time.time()),
                "model": model,
                "video_url": video_url,
                "url": video_url,
                "status": "completed",
                "seed": seed,
            }

        # Fallback: Check if Wan2GP has output files directly
        video_url = await self._check_output_directory()
        if video_url:
            return {
                "id": f"video-{int(time.time())}",
                "created": int(time.time()),
                "model": model,
                "video_url": video_url,
                "url": video_url,
                "status": "completed",
                "seed": seed,
            }

        logger.warning("Wan2GP: Could not retrieve video URL")
        return {
            "error": "Video generation started but URL not found. Check Wan2GP web UI.",
            "webui_url": self.base_url,
        }

    async def _poll_gallery_for_video(
        self,
        timeout: int = 600,
        poll_interval: int = 10,
    ) -> Optional[str]:
        """
        Poll _refresh_gallery for generated videos.

        _refresh_gallery has 3 params: [refresh_id, paths_json, selected_idx]
        """
        start_time = time.time()
        attempts = 0

        while time.time() - start_time < timeout:
            attempts += 1
            elapsed = int(time.time() - start_time)
            logger.debug(
                f"Wan2GP: Gallery poll #{attempts} ({elapsed}s elapsed)"
            )

            # Call _refresh_gallery
            result = await self._call_gradio_endpoint(
                "/_refresh_gallery",
                ["", [], -1],
                timeout=30.0,
            )

            if result and isinstance(result, tuple):
                _, gallery_data = result
                video_url = self._extract_video_url(gallery_data)
                if video_url:
                    return video_url

            await asyncio.sleep(poll_interval)

        return None

    def _extract_video_url(self, data) -> Optional[str]:
        """
        Recursively extract video URL from Gradio gallery response.

        Gallery data can be nested lists/tuples of file objects.
        """
        if not data:
            return None

        # Handle tuple/list
        if isinstance(data, (tuple, list)):
            for item in data:
                url = self._extract_video_url(item)
                if url:
                    return url
            return None

        # Handle dict (file object)
        if isinstance(data, dict):
            orig_name = data.get("orig_name", "")
            if orig_name.lower().endswith((".mp4", ".webm", ".avi", ".gif", ".mov")):
                # Check for URL field
                url = data.get("url", "")
                if url:
                    # Make absolute if needed
                    if url.startswith("/"):
                        return f"{self.base_url}{url}"
                    return url

                # Check for path field (Gradio file serving)
                path = data.get("path", "")
                if path:
                    return f"{self.base_url}/gradio_api/file={path}"

            # Check nested data
            for key in ("video", "image", "data", "value"):
                if key in data:
                    url = self._extract_video_url(data[key])
                    if url:
                        return url

        # Handle string URL
        if isinstance(data, str):
            if data.lower().endswith((".mp4", ".webm", ".gif", ".mov")):
                if data.startswith("http"):
                    return data
                if data.startswith("/"):
                    return f"{self.base_url}{data}"

        return None

    async def _check_output_directory(self) -> Optional[str]:
        """
        Check if Wan2GP has output files in its output directory.
        This is a fallback when gallery polling fails.
        """
        # Wan2GP typically saves to an output folder
        # Try common paths via the file serving API
        output_paths = [
            "/output/",
            "/gradio_api/file=output/",
        ]

        # We can't easily list directories via HTTP, so just return None
        # The gallery polling should handle this
        return None

    async def close(self):
        """Close HTTP clients."""
        await self.client.aclose()
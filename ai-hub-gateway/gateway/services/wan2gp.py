
"""
Wan2GP Service Connector.
Uses gradio_client to interface with Wan2GP's complex Gradio 5.x API.
The Gateway runs locally on the NAB9, so gradio_client connects to localhost.
"""
import logging
import time
import asyncio
import os
from typing import Dict, Optional

import httpx

from ..config import WAN2GP_BASE_URL

logger = logging.getLogger(__name__)

# Check if gradio_client is available
try:
    from gradio_client import Client as GradioClient
    GRADIO_CLIENT_AVAILABLE = True
except ImportError:
    GRADIO_CLIENT_AVAILABLE = False
    logger.warning("gradio_client not installed. Video generation will use redirect mode.")


class Wan2GPService:
    """Service connector for Wan2GP video generation via Gradio Client."""

    def __init__(self, base_url: str = WAN2GP_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)
        self._gradio_client = None
        self._gradio_lock = asyncio.Lock()

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

    async def _get_gradio_client(self) -> Optional["GradioClient"]:
        """Get or create a gradio_client connection (thread-safe)."""
        if not GRADIO_CLIENT_AVAILABLE:
            return None

        async with self._gradio_lock:
            if self._gradio_client is None:
                try:
                    # Connect in a thread (gradio_client is sync)
                    self._gradio_client = await asyncio.to_thread(
                        GradioClient, self.base_url
                    )
                    logger.info(f"Gradio client connected to {self.base_url}")
                except Exception as e:
                    logger.error(f"Failed to connect gradio_client: {e}")
                    self._gradio_client = None
            return self._gradio_client

    async def _reset_gradio_client(self):
        """Reset the gradio client (on error)."""
        async with self._gradio_lock:
            self._gradio_client = None

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
        
        Uses gradio_client to interface with the complex Gradio 5.x API.
        Wan2GP's UI has 488 functions with deep UI state dependencies,
        so we use gradio_client which handles session management.
        
        Falls back to redirect mode if gradio_client is unavailable.
        """
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        # ── STRATEGY 1: Use gradio_client (best for this complex API) ──
        if GRADIO_CLIENT_AVAILABLE:
            try:
                result = await self._generate_via_gradio_client(
                    prompt=prompt,
                    model=model,
                    width=width,
                    height=height,
                    frames=frames,
                    steps=steps,
                    cfg_scale=cfg_scale,
                    seed=seed,
                )
                if result and "error" not in result:
                    return result
                if result:
                    logger.warning(f"gradio_client returned error: {result.get('error')}")
            except Exception as e:
                logger.error(f"gradio_client generation failed: {e}")
                await self._reset_gradio_client()

        # ── STRATEGY 2: Try raw HTTP (Gradio 5.x SSE format) ──
        try:
            result = await self._generate_via_http(prompt, model, seed)
            if result and "error" not in result:
                return result
        except Exception as e:
            logger.error(f"HTTP generation failed: {e}")

        # ── FALLBACK: Redirect to web UI ──
        logger.warning("All generation strategies failed, returning redirect")
        return {
            "id": f"video-{int(time.time())}",
            "status": "redirect",
            "model": model,
            "seed": seed,
            "message": "Wan2GP video generation requires the web UI for this configuration.",
            "webui_url": self.base_url,
            "prompt": prompt,
        }

    async def _generate_via_gradio_client(
        self,
        prompt: str,
        model: str = "wan2.1",
        width: int = 832,
        height: int = 480,
        frames: int = 81,
        steps: int = 20,
        cfg_scale: float = 6.0,
        seed: int = -1,
    ) -> Dict:
        """
        Generate video using gradio_client.
        
        Wan2GP flow:
        1. fill_wizard_prompt - sets the prompt in the UI
        2. process_prompt_and_add_tasks - adds to generation queue
        3. prepare_generate_video - starts the generation
        4. Poll refresh_gallery for output video
        """
        client = await self._get_gradio_client()
        if not client:
            return {"error": "gradio_client not connected"}

        # Step 1: Fill the prompt
        logger.info(f"Wan2GP: Setting prompt '{prompt[:50]}...'")
        try:
            await asyncio.to_thread(
                client.predict,
                "",  # variables
                prompt,  # the prompt text
                "",  # additional context
                "",  # extra
                api_name="/fill_wizard_prompt",
            )
        except Exception as e:
            logger.warning(f"fill_wizard_prompt failed (may be ok): {e}")

        # Step 2: Add task to queue
        logger.info("Wan2GP: Adding task to queue...")
        try:
            await asyncio.to_thread(
                client.predict,
                0,       # current_gallery_tab
                prompt,  # prompt text
                "",      # extra state
                api_name="/process_prompt_and_add_tasks",
            )
        except Exception as e:
            logger.warning(f"process_prompt_and_add_tasks failed: {e}")

        # Step 3: Start generation
        logger.info("Wan2GP: Starting generation...")
        try:
            await asyncio.to_thread(
                client.predict,
                api_name="/prepare_generate_video",
            )
        except Exception as e:
            logger.warning(f"prepare_generate_video failed: {e}")

        # Step 4: Poll gallery for output video
        logger.info("Wan2GP: Waiting for video output (polling gallery)...")
        video_url = await self._poll_gradio_gallery(client, timeout=600)

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

        return {"error": "Video generation timed out waiting for output"}

    async def _poll_gradio_gallery(
        self,
        client: "GradioClient",
        timeout: int = 600,
    ) -> Optional[str]:
        """
        Poll the Wan2GP gallery for generated videos.
        
        Wan2GP stores output videos in its gallery. We call refresh_gallery
        and look for video file URLs.
        """
        start_time = time.time()
        check_interval = 5  # seconds

        while time.time() - start_time < timeout:
            try:
                # Call refresh_gallery to get current gallery state
                result = await asyncio.to_thread(
                    client.predict,
                    api_name="/refresh_gallery",
                )

                # Parse result for video URLs
                video_url = self._extract_video_from_gallery(result)
                if video_url:
                    logger.info(f"Wan2GP: Video found: {video_url}")
                    return video_url

            except Exception as e:
                logger.debug(f"Gallery poll error: {e}")

            await asyncio.sleep(check_interval)

        return None

    def _extract_video_from_gallery(self, result) -> Optional[str]:
        """
        Extract video URL from Wan2GP gallery response.
        
        Gallery response can be:
        - List of file objects: [{"path": "...", "url": "...", "orig_name": "..."}]
        - Tuple with gallery data
        - None (no videos yet)
        """
        if not result:
            return None

        # Handle tuple (gradio often returns tuples)
        if isinstance(result, (tuple, list)):
            for item in result:
                url = self._extract_video_from_gallery(item)
                if url:
                    return url
            return None

        # Handle dict (file object)
        if isinstance(result, dict):
            # Check for video file
            orig_name = result.get("orig_name", "")
            if orig_name.endswith((".mp4", ".webm", ".avi", ".gif", ".mov")):
                url = result.get("url", "")
                if url:
                    return url
                path = result.get("path", "")
                if path:
                    return f"{self.base_url}/gradio_api/file={path}"

            # Check nested data
            for key in ("video", "image", "data"):
                if key in result:
                    url = self._extract_video_from_gallery(result[key])
                    if url:
                        return url

        # Handle string URL
        if isinstance(result, str):
            if result.startswith("http") and result.endswith((".mp4", ".webm", ".gif")):
                return result

        return None

    async def _generate_via_http(self, prompt: str, model: str, seed: int) -> Dict:
        """
        Try raw HTTP Gradio 5.x API as fallback.
        Uses /gradio_api/call/ endpoint with SSE polling.
        """
        long_client = httpx.AsyncClient(timeout=600.0)
        try:
            # Submit to /gradio_api/call/generate
            resp = await long_client.post(
                f"{self.base_url}/gradio_api/call/generate",
                json={
                    "data": [
                        prompt,     # prompt text
                        "",         # negative
                        model,      # model
                        832,        # width
                        480,        # height
                        81,         # frames
                        20,         # steps
                        6.0,        # cfg
                        seed,       # seed
                    ]
                },
                timeout=30.0,
            )

            if resp.status_code != 200:
                return {"error": f"HTTP submit returned {resp.status_code}"}

            event_data = resp.json()
            event_id = event_data.get("event_id")
            if not event_id:
                return {"error": "No event_id in response"}

            # Poll SSE for result
            sse_url = f"{self.base_url}/gradio_api/call/generate/{event_id}"
            video_url = await self._poll_sse(long_client, sse_url)

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

            return {"error": "SSE polling timed out"}
        finally:
            await long_client.aclose()

    async def _poll_sse(self, client: httpx.AsyncClient, url: str, timeout: int = 600) -> Optional[str]:
        """Poll SSE endpoint for video result."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with client.stream("GET", url, timeout=30.0) as resp:
                    if resp.status_code != 200:
                        await asyncio.sleep(2)
                        continue

                    event_type = None
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                        elif line.startswith("data:"):
                            import json
                            data_str = line[5:].strip()
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            if event_type == "complete":
                                return self._extract_video_from_gallery(data)
                            elif event_type == "error":
                                logger.error(f"Gradio SSE error: {data}")
                                return None
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                continue
            except Exception as e:
                logger.debug(f"SSE poll error: {e}")
                await asyncio.sleep(2)

        return None

    async def close(self):
        """Close HTTP clients."""
        await self.client.aclose()
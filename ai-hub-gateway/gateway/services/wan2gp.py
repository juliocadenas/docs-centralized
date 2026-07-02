"""
Wan2GP Service Connector v2.
Uses gradio_client via subprocess to handle Gradio 5.x sessions correctly.

The generator script runs as a subprocess, avoiding async/sync conflicts.
"""
import logging
import asyncio
import json
import os
import time
from typing import Dict, Optional
from pathlib import Path

import httpx

from ..config import WAN2GP_BASE_URL

logger = logging.getLogger(__name__)

# Path to the standalone generator script
GENERATOR_SCRIPT = Path(__file__).parent / "wan2gp_generator.py"


class Wan2GPService:
    """Service connector for Wan2GP video generation via gradio_client subprocess."""

    def __init__(self, base_url: str = WAN2GP_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def health_check(self) -> Dict:
        """Check if Wan2GP is running."""
        try:
            start = time.time()
            resp = await self.client.get(f"{self.base_url}/config", timeout=10.0)
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
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
        Generate video via Wan2GP using gradio_client subprocess.

        The generator script handles:
        1. Connect to Wan2GP with fresh session
        2. process_prompt_and_add_tasks (model_mode='t2v')
        3. init_generate
        4. prepare_generate_video
        5. Poll refresh_gallery for output video URL
        """
        # Check service health first
        health = await self.health_check()
        if health.get("status") != "online":
            return {
                "error": f"Wan2GP is {health.get('status')}: {health.get('error', '')}",
                "webui_url": self.base_url,
            }

        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        logger.info(f"Wan2GP: Starting generation for '{prompt[:60]}...'")

        # Build subprocess command
        cmd = [
            "python",
            str(GENERATOR_SCRIPT),
            "--base-url", self.base_url,
            "--prompt", prompt,
            "--negative-prompt", negative_prompt,
            "--width", str(width),
            "--height", str(height),
            "--frames", str(frames),
            "--steps", str(steps),
            "--cfg", str(cfg_scale),
            "--seed", str(seed),
            "--timeout", "600",
        ]

        logger.info(f"Wan2GP: Running generator subprocess: {' '.join(cmd[:6])}...")

        try:
            # Run subprocess with timeout (660s = 11min, generator has 600s internal)
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=660.0)

            if proc.returncode != 0:
                err_msg = stderr.decode("utf-8", errors="replace")[:500]
                logger.error(f"Wan2GP generator failed (exit {proc.returncode}): {err_msg}")
                return {
                    "error": f"Generator process failed: {err_msg[:200]}",
                    "webui_url": self.base_url,
                }

            # Parse JSON result from stdout
            output = stdout.decode("utf-8", errors="replace").strip()
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Log stderr for debugging
            if stderr_str:
                for line in stderr_str.strip().split("\n")[-5:]:  # Last 5 lines
                    logger.info(f"Wan2GP generator: {line}")

            try:
                result = json.loads(output.split("\n")[-1])  # Last line is JSON
            except json.JSONDecodeError:
                logger.error(f"Wan2GP: Could not parse generator output: {output[:300]}")
                return {
                    "error": "Generator produced invalid output",
                    "raw_output": output[:500],
                    "webui_url": self.base_url,
                }

            if result.get("status") == "completed":
                video_url = result.get("video_url", "")
                logger.info(f"Wan2GP: Video ready at {video_url} ({result.get('elapsed_seconds', '?')}s)")
                return {
                    "id": f"video-{int(time.time())}",
                    "created": int(time.time()),
                    "model": model,
                    "video_url": video_url,
                    "url": video_url,
                    "status": "completed",
                    "seed": seed,
                }
            else:
                logger.error(f"Wan2GP: Generation failed: {result}")
                return {
                    "error": result.get("error", "Unknown error"),
                    "webui_url": self.base_url,
                }

        except asyncio.TimeoutError:
            logger.error("Wan2GP: Subprocess timed out after 660s")
            return {
                "error": "Video generation timed out (660s)",
                "webui_url": self.base_url,
            }
        except Exception as e:
            logger.error(f"Wan2GP: Unexpected error: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "webui_url": self.base_url,
            }

    async def close(self):
        """Close HTTP clients."""
        await self.client.aclose()
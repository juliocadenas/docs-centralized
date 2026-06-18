"""
DocuMusic Service Connector.
Proxies audio/music generation requests to DocuMusic backend.
"""
import logging
import time
from typing import Dict, Optional

import httpx

from ..config import DOCUMUSIC_BASE_URL

logger = logging.getLogger(__name__)


class DocuMusicService:
    """Service connector for DocuMusic audio generation."""

    def __init__(self, base_url: str = DOCUMUSIC_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=300.0)

    async def health_check(self) -> Dict:
        """Check if DocuMusic is running."""
        try:
            start = time.time()
            resp = await self.client.get(f"{self.base_url}/health")
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                return {"status": "online", "response_time_ms": elapsed}
            return {"status": "error", "error": f"HTTP {resp.status_code}"}
        except httpx.ConnectError:
            return {"status": "offline", "error": "Connection refused"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def generate_audio(
        self,
        model: str = "ace-step",
        prompt: Optional[str] = None,
        lyrics: Optional[str] = None,
        tags: str = "",
        duration_seconds: int = 30,
        seed: int = -1,
        steps: Optional[int] = None,
        cfg_scale: Optional[float] = None,
    ) -> Dict:
        """Generate audio/music via DocuMusic backend."""
        try:
            # Build the request payload based on DocuMusic's API
            payload = {
                "model": model,
                "tags": tags,
                "duration_seconds": duration_seconds,
            }

            if prompt:
                payload["prompt"] = prompt
            if lyrics:
                payload["lyrics"] = lyrics
            if seed != -1:
                payload["seed"] = seed
            if steps:
                payload["steps"] = steps
            if cfg_scale:
                payload["cfg_scale"] = cfg_scale

            resp = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300.0,
            )

            if resp.status_code == 200:
                data = resp.json()
                return {
                    "id": data.get("id", f"audio-{int(time.time())}"),
                    "status": "processing",
                    "model": model,
                    "audio_url": data.get("audio_url"),
                    "message": "Audio generation started",
                }
            else:
                return {
                    "error": f"DocuMusic returned HTTP {resp.status_code}: {resp.text}"
                }

        except httpx.ConnectError:
            return {"error": "DocuMusic service is not available."}
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            return {"error": str(e)}

    async def get_status(self, job_id: str) -> Dict:
        """Check status of an audio generation job."""
        try:
            resp = await self.client.get(f"{self.base_url}/api/status/{job_id}")
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def list_models(self) -> list:
        """List available audio models from DocuMusic."""
        try:
            resp = await self.client.get(f"{self.base_url}/api/models")
            if resp.status_code == 200:
                return resp.json().get("models", [])
            return []
        except Exception:
            # Return static list as fallback
            return [
                {"id": "yue", "name": "YuE", "type": "text-to-music"},
                {"id": "ace-step", "name": "ACE-Step v1 3.5B", "type": "text-to-music"},
                {"id": "diffrhythm", "name": "DiffRhythm v2", "type": "text-to-music"},
            ]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
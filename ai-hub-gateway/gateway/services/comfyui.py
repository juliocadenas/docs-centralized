"""
ComfyUI Service Connector.
Proxies image generation requests to ComfyUI API.
"""
import logging
import time
import uuid
from typing import Dict, List, Optional

import httpx

from ..config import COMFYUI_BASE_URL

logger = logging.getLogger(__name__)


class ComfyUIService:
    """Service connector for ComfyUI image/video generation."""

    def __init__(self, base_url: str = COMFYUI_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=300.0)

    async def health_check(self) -> Dict:
        """Check if ComfyUI is running."""
        try:
            start = time.time()
            resp = await self.client.get(f"{self.base_url}/system_stats")
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                return {"status": "online", "response_time_ms": elapsed}
            return {"status": "error", "error": f"HTTP {resp.status_code}"}
        except httpx.ConnectError:
            return {"status": "offline", "error": "Connection refused"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_system_stats(self) -> Dict:
        """Get ComfyUI system stats including VRAM usage."""
        try:
            resp = await self.client.get(f"{self.base_url}/system_stats")
            if resp.status_code == 200:
                return resp.json()
            return {}
        except Exception as e:
            logger.error(f"Failed to get ComfyUI stats: {e}")
            return {}

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.0,
        seed: int = -1,
        sampler: str = "euler",
        scheduler: str = "normal",
        model: str = "sd15",
    ) -> Dict:
        """
        Generate an image via ComfyUI API.
        Creates a simple txt2img workflow and submits it.
        """
        try:
            # Determine checkpoint based on model
            checkpoint_map = {
                "sd15": "v1-5-pruned-emaonly.safetensors",
                "sdxl": "sd_xl_base_1.0.safetensors",
                "sdxl-turbo": "sd_xl_turbo_1.0.safetensors",
                "flux-schnell": "flux1-schnell.safetensors",
            }
            checkpoint = checkpoint_map.get(model, model)

            # Override steps for turbo models if not specified
            if model == "sdxl-turbo" and steps == 20:
                steps = 1  # SDXL Turbo default: 1 step
            elif model == "flux-schnell" and steps == 20:
                steps = 4  # FLUX Schnell default: 4 steps

            # Turbo models don't use negative prompts or high CFG
            if model == "sdxl-turbo":
                cfg_scale = min(cfg_scale, 1.0)  # SDXL Turbo needs CFG <= 1.0
            elif model == "flux-schnell":
                cfg_scale = 0.0  # FLUX schnell needs CFG = 0

            if seed == -1:
                import random
                seed = random.randint(0, 2**32 - 1)

            # Build a basic ComfyUI workflow for txt2img
            workflow = _build_txt2img_workflow(
                checkpoint=checkpoint,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg=cfg_scale,
                seed=seed,
                sampler_name=sampler,
                scheduler=scheduler,
            )

            # Submit workflow
            resp = await self.client.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow},
                timeout=60.0,
            )

            if resp.status_code == 200:
                data = resp.json()
                prompt_id = data.get("prompt_id")
                return {
                    "id": prompt_id,
                    "status": "processing",
                    "seed": seed,
                    "message": f"Image generation submitted. Prompt ID: {prompt_id}",
                    "check_status": f"/v1/images/status/{prompt_id}",
                }
            else:
                return {
                    "error": f"ComfyUI returned HTTP {resp.status_code}: {resp.text}"
                }

        except httpx.ConnectError:
            return {"error": "ComfyUI service is not available."}
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return {"error": str(e)}

    async def get_prompt_status(self, prompt_id: str) -> Dict:
        """Check the status of a submitted prompt."""
        try:
            resp = await self.client.get(f"{self.base_url}/history/{prompt_id}")
            if resp.status_code == 200:
                history = resp.json()
                if prompt_id in history:
                    status = history[prompt_id].get("status", {})
                    outputs = history[prompt_id].get("outputs", {})

                    # Extract output images
                    images = []
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            for img in node_output["images"]:
                                images.append({
                                    "filename": img["filename"],
                                    "subfolder": img.get("subfolder", ""),
                                    "type": img.get("type", "output"),
                                    "url": f"{self.base_url}/view?filename={img['filename']}",
                                })

                    return {
                        "prompt_id": prompt_id,
                        "status": "completed" if status.get("completed", False) or status.get("status_str") == "success" else "processing",
                        "images": images,
                    }
                return {"prompt_id": prompt_id, "status": "not_found"}
            return {"prompt_id": prompt_id, "status": "error"}
        except Exception as e:
            return {"prompt_id": prompt_id, "status": "error", "error": str(e)}

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def _build_txt2img_workflow(
    checkpoint: str,
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    seed: int,
    sampler_name: str,
    scheduler: str,
) -> Dict:
    """Build a basic ComfyUI txt2img workflow."""
    return {
        "3": {  # KSampler
            "class_type": "KSampler",
            "inputs": {
                "cfg": cfg,
                "denoise": 1.0,
                "latent_image": ["5", 0],
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "seed": seed,
                "steps": steps,
            }
        },
        "4": {  # Checkpoint Loader
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": checkpoint,
            }
        },
        "5": {  # Empty Latent Image
            "class_type": "EmptyLatentImage",
            "inputs": {
                "batch_size": 1,
                "height": height,
                "width": width,
            }
        },
        "6": {  # CLIP Text Encode (positive)
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": prompt,
            }
        },
        "7": {  # CLIP Text Encode (negative)
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": negative_prompt,
            }
        },
        "8": {  # VAE Decode
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2],
            }
        },
        "9": {  # Save Image
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "AIHub",
                "images": ["8", 0],
            }
        },
    }
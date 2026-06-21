"""
Ollama Service Connector.
Proxies chat completion requests to Ollama, converting to OpenAI format.
"""
import asyncio
import logging
import time
import uuid
from typing import AsyncIterator, Dict, List, Optional

import httpx

from ..config import OLLAMA_BASE_URL

logger = logging.getLogger(__name__)


class OllamaService:
    """Service connector for Ollama LLM."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)

    async def health_check(self) -> Dict:
        """Check if Ollama is running and return status."""
        try:
            start = time.time()
            resp = await self.client.get(f"{self.base_url}/api/tags")
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                return {"status": "online", "response_time_ms": elapsed}
            return {"status": "error", "error": f"HTTP {resp.status_code}"}
        except httpx.ConnectError:
            return {"status": "offline", "error": "Connection refused"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def list_models(self) -> List[Dict]:
        """List available models from Ollama."""
        try:
            resp = await self.client.get(f"{self.base_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = []
                for model in data.get("models", []):
                    models.append({
                        "id": model["name"],
                        "object": "model",
                        "created": 0,
                        "owned_by": "ai-hub-madrid",
                        "type": "llm",
                        "service": "ollama",
                        "status": "available",
                    })
                return models
            return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        stop: Optional[str] = None,
        options: Optional[Dict] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Send a chat completion request to Ollama and return OpenAI-formatted response.
        
        Ollama has its own /api/chat endpoint, but we also support /v1/chat/completions
        which Ollama natively supports in newer versions.
        """
        try:
            # Build payload - prefer options dict if provided (more flexible)
            if options:
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                }
                # Map common options to OpenAI format
                if "temperature" in options:
                    payload["temperature"] = options["temperature"]
                if "top_p" in options:
                    payload["top_p"] = options["top_p"]
                if "num_predict" in options:
                    payload["max_tokens"] = options["num_predict"]
                if "stop" in options:
                    payload["stop"] = options["stop"] if isinstance(options["stop"], list) else [options["stop"]]
                if "seed" in options:
                    payload["seed"] = options["seed"]
                if "frequency_penalty" in options:
                    payload["frequency_penalty"] = options["frequency_penalty"]
                if "presence_penalty" in options:
                    payload["presence_penalty"] = options["presence_penalty"]
            else:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "top_p": top_p,
                    "stream": False,
                }
                if max_tokens:
                    payload["max_tokens"] = max_tokens
                if stop:
                    payload["stop"] = stop if isinstance(stop, list) else [stop]

            # Add tools (function calling) if provided
            if tools:
                payload["tools"] = tools

            resp = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=120.0,
            )

            if resp.status_code == 200:
                # Ollama's OpenAI-compatible endpoint returns the right format
                return resp.json()
            else:
                # Fallback to Ollama native API
                logger.warning(
                    f"Ollama OpenAI endpoint returned {resp.status_code}, "
                    f"falling back to native API"
                )
                return await self._native_chat(model, messages, temperature, top_p)

        except httpx.ConnectError:
            return {
                "error": "Ollama service is not available. "
                         "Please ensure Ollama is running on the server."
            }
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            return {"error": str(e)}

    async def _native_chat(
        self,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> Dict:
        """Fallback: Use Ollama native /api/chat endpoint and convert response."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
        }

        resp = await self.client.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120.0,
        )

        if resp.status_code == 200:
            data = resp.json()
            # Convert Ollama native format to OpenAI format
            return {
                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": data.get("message", {}).get("content", ""),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": (
                        data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    ),
                },
            }
        else:
            return {"error": f"Ollama returned HTTP {resp.status_code}: {resp.text}"}

    async def chat_completion_stream(
        self,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        stop: Optional[str] = None,
        options: Optional[Dict] = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion tokens as Server-Sent Events (SSE).
        
        Yields OpenAI-compatible SSE chunks:
        data: {"choices":[{"delta":{"content":"token"}}]}
        """
        chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())

        if options:
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
            }
            if "temperature" in options:
                payload["temperature"] = options["temperature"]
            if "top_p" in options:
                payload["top_p"] = options["top_p"]
            if "num_predict" in options:
                payload["max_tokens"] = options["num_predict"]
            if "stop" in options:
                payload["stop"] = options["stop"] if isinstance(options["stop"], list) else [options["stop"]]
            if "seed" in options:
                payload["seed"] = options["seed"]
        else:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "stream": True,
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens
            if stop:
                payload["stop"] = stop if isinstance(stop, list) else [stop]

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=120.0,
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    error_data = {
                        "error": f"Ollama returned {resp.status_code}: {body.decode()[:200]}"
                    }
                    yield f"data: {__import__('json').dumps(error_data)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str.strip() == "[DONE]":
                        yield "data: [DONE]\n\n"
                        return
                    try:
                        import json
                        chunk = json.loads(data_str)
                        # Re-wrap with our chat_id for consistency
                        chunk["id"] = chat_id
                        chunk["created"] = created
                        yield f"data: {json.dumps(chunk)}\n\n"
                    except Exception:
                        continue

            yield "data: [DONE]\n\n"

        except httpx.ConnectError:
            import json
            error = {"error": "Ollama service is not available."}
            yield f"data: {json.dumps(error)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            import json
            logger.error(f"Streaming error: {e}")
            error = {"error": str(e)}
            yield f"data: {json.dumps(error)}\n\n"
            yield "data: [DONE]\n\n"

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

"""
LLM Router - OpenAI-compatible chat completions endpoint.
Proxies to Ollama service.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..models.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from ..services.ollama import OllamaService

logger = logging.getLogger(__name__)
router = APIRouter()

# Service instance (initialized in main.py)
ollama_service: OllamaService = None


def set_service(service: OllamaService):
    global ollama_service
    ollama_service = service


class EmbeddingRequest(BaseModel):
    """OpenAI-compatible embeddings request."""
    model: str = "nomic-embed-text"
    input: Any  # Accept str or list[str] (OpenAI compatible)


class WarmModelRequest(BaseModel):
    """Request to pre-load a model into VRAM."""
    model: str


class VisionRequest(BaseModel):
    """Analyze an image with a vision LLM."""
    model: str = "qwen2.5vl:7b"
    image_url: str
    prompt: str = "Describe esta imagen en detalle."


def _build_options(request: ChatCompletionRequest) -> dict:
    """Build options dict from request fields."""
    options = {}
    if request.temperature is not None:
        options["temperature"] = request.temperature
    if request.top_p is not None:
        options["top_p"] = request.top_p
    if request.max_tokens is not None:
        options["num_predict"] = request.max_tokens
    if request.seed is not None:
        options["seed"] = request.seed
    if request.stop is not None:
        options["stop"] = request.stop
    if request.frequency_penalty is not None:
        options["frequency_penalty"] = request.frequency_penalty
    if request.presence_penalty is not None:
        options["presence_penalty"] = request.presence_penalty
    return options


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """
    Create a chat completion (OpenAI-compatible).
    
    Proxies the request to Ollama and returns in OpenAI format.
    Compatible with the OpenAI Python client library.
    """
    if not ollama_service:
        raise HTTPException(status_code=503, detail="LLM service not initialized")

    messages = []
    for m in request.messages:
        msg = {"role": m.role, "content": m.content}
        if m.name:
            msg["name"] = m.name
        messages.append(msg)

    options = _build_options(request)

    # Handle JSON mode
    if request.response_format and request.response_format.get("type") == "json_object":
        messages.insert(0, {
            "role": "system",
            "content": "You must respond with valid JSON only. No markdown, no code fences.",
        })

    result = await ollama_service.chat_completion(
        model=request.model,
        messages=messages,
        options=options if options else None,
        stream=request.stream,
        tools=request.tools,
    )

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    if "choices" in result:
        return result

    raise HTTPException(status_code=502, detail="Unexpected response from Ollama")


@router.post("/chat/completions/stream")
async def create_chat_completion_stream(request: ChatCompletionRequest):
    """
    Stream a chat completion via Server-Sent Events (SSE).
    
    Returns text/event-stream with OpenAI-compatible chunks.
    The frontend can consume this with EventSource or fetch + ReadableStream.
    """
    if not ollama_service:
        raise HTTPException(status_code=503, detail="LLM service not initialized")

    if not request.stream:
        return await create_chat_completion(request)

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    options = _build_options(request)

    return StreamingResponse(
        ollama_service.chat_completion_stream(
            model=request.model,
            messages=messages,
            options=options if options else None,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings (OpenAI-compatible /v1/embeddings).
    
    Requires an embedding model in Ollama (e.g. nomic-embed-text).
    """
    if not ollama_service:
        raise HTTPException(status_code=503, detail="LLM service not initialized")

    # Normalize input to list (OpenAI accepts string or list[str])
    texts = request.input if isinstance(request.input, list) else [request.input]

    result = await ollama_service.embeddings(
        model=request.model,
        input=texts,
    )

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result


@router.post("/models/warm")
async def warm_model(request: WarmModelRequest):
    """
    Pre-load a model into VRAM (warm-up).
    
    Sends a tiny request so the model is loaded before the user uses it.
    Reduces first-request latency significantly.
    """
    if not ollama_service:
        raise HTTPException(status_code=503, detail="LLM service not initialized")

    result = await ollama_service.warm_model(request.model)

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result


@router.post("/chat/vision")
async def analyze_image(request: VisionRequest):
    """
    Analyze an image with a vision LLM (qwen2.5vl, llava, etc).
    
    Sends the image URL and prompt to the vision model.
    Works with Ollama's multimodal chat endpoint.
    """
    if not ollama_service:
        raise HTTPException(status_code=503, detail="LLM service not initialized")

    messages = [{
        "role": "user",
        "content": request.prompt,
        "images": [request.image_url],
    }]

    try:
        result = await ollama_service.chat_completion(
            model=request.model,
            messages=messages,
        )
    except Exception as e:
        logger.error(f"Vision analysis error: {e}")
        raise HTTPException(status_code=502, detail=f"Vision model error: {str(e)}")

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result
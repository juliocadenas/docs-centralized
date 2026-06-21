"""
LLM Router - OpenAI-compatible chat completions endpoint.
Proxies to Ollama service.
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
    UsageInfo,
)
from ..services.ollama import OllamaService

logger = logging.getLogger(__name__)
router = APIRouter()

# Service instance (initialized in main.py)
ollama_service: OllamaService = None


def set_service(service: OllamaService):
    global ollama_service
    ollama_service = service


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """
    Create a chat completion (OpenAI-compatible).
    
    Proxies the request to Ollama and returns in OpenAI format.
    Compatible with the OpenAI Python client library.
    """
    if not ollama_service:
        raise HTTPException(status_code=503, detail="LLM service not initialized")

    # Convert messages to dict format
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Build options dict for Ollama (supports seed, penalties, etc.)
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

    # If Ollama returned OpenAI format directly, pass through
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
        # If client didn't request stream, redirect to non-stream endpoint
        return await create_chat_completion(request)

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Build options
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
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )

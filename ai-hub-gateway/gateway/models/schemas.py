"""
Pydantic schemas for OpenAI-compatible API.
These models match the OpenAI API format for maximum compatibility.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ============================================================
# Chat Completions (OpenAI-compatible)
# ============================================================
class ChatMessage(BaseModel):
    role: str
    # Support both string content and multimodal list (vision)
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str = "qwen2.5:7b"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    # OpenAI extensions (passed through to Ollama where supported)
    seed: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = None
    response_format: Optional[Dict[str, Any]] = None  # {"type": "json_object"}
    n: Optional[int] = 1


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo = UsageInfo()


# ============================================================
# Image Generation (OpenAI-compatible)
# ============================================================
class ImageGenerationRequest(BaseModel):
    model: Optional[str] = "sd15"
    prompt: str
    negative_prompt: Optional[str] = ""
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"  # width x height
    response_format: Optional[str] = "url"  # "url" or "b64_json"
    steps: Optional[int] = 20
    cfg_scale: Optional[float] = 7.0
    seed: Optional[int] = -1
    sampler: Optional[str] = "euler"
    scheduler: Optional[str] = "normal"


class ImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None


class ImageGenerationResponse(BaseModel):
    created: int
    data: List[ImageData]


# ============================================================
# Audio Generation
# ============================================================
class AudioGenerationRequest(BaseModel):
    model: Optional[str] = "ace-step"
    prompt: Optional[str] = None
    lyrics: Optional[str] = None
    tags: Optional[str] = ""
    duration_seconds: Optional[int] = 30
    seed: Optional[int] = -1
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None


class AudioGenerationResponse(BaseModel):
    id: str
    created: int
    model: str
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    status: str = "processing"


# ============================================================
# Video Generation
# ============================================================
class VideoGenerationRequest(BaseModel):
    model: Optional[str] = "wan2.1"
    prompt: str
    negative_prompt: Optional[str] = ""
    width: Optional[int] = 832
    height: Optional[int] = 480
    frames: Optional[int] = 81
    steps: Optional[int] = 20
    cfg_scale: Optional[float] = 6.0
    seed: Optional[int] = -1
    sampler: Optional[str] = None
    scheduler: Optional[str] = None


class VideoGenerationResponse(BaseModel):
    id: str
    created: int
    model: str
    video_url: Optional[str] = None
    duration: Optional[float] = None
    status: str = "processing"


# ============================================================
# Models (OpenAI-compatible)
# ============================================================
class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "ai-hub-madrid"
    type: Optional[str] = None
    service: Optional[str] = None
    vram_mb: Optional[int] = None
    status: Optional[str] = None


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelInfo] = []


# ============================================================
# Status & Infrastructure
# ============================================================
class ServiceStatus(BaseModel):
    name: str
    status: str  # "online", "offline", "starting", "error"
    url: str
    port: int
    type: str
    categories: List[str]
    vram_mb: int
    always_on: bool
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


class GPUInfo(BaseModel):
    total_vram_mb: int
    used_vram_mb: Optional[int] = None
    free_vram_mb: Optional[int] = None
    gpu_name: Optional[str] = None
    gpu_utilization: Optional[float] = None
    temperature: Optional[float] = None


class SystemStatus(BaseModel):
    status: str = "ok"
    gateway_version: str
    uptime_seconds: float
    services: List[ServiceStatus]
    gpu: Optional[GPUInfo] = None
    timestamp: str


class InfrastructureInfo(BaseModel):
    """Full infrastructure map served via API."""
    gateway: Dict[str, Any]
    server: Dict[str, Any]
    services: List[ServiceStatus]
    gpu: Optional[GPUInfo] = None
    storage: Dict[str, Any]
    network: Dict[str, Any]
    models_count: int
    timestamp: str


# ============================================================
# Voice - TTS (Text-to-Speech) & STT (Speech-to-Text)
# OpenAI-compatible: /v1/audio/speech and /v1/audio/transcriptions
# ============================================================
class SpeechRequest(BaseModel):
    """OpenAI-compatible TTS request.
    Supports multiple engines: piper (default), xtts, fish.
    """
    model: Optional[str] = "piper"  # piper, xtts, fish
    input: str
    voice: Optional[str] = "es_ES-davefx-medium"
    response_format: Optional[str] = "wav"  # wav, mp3
    speed: Optional[float] = 1.0
    language: Optional[str] = "es"
    # XTTS-v2 voice cloning: path or URL to reference speaker audio
    speaker_wav: Optional[str] = None


class TranscriptionRequest(BaseModel):
    """OpenAI-compatible STT request."""
    model: Optional[str] = "whisper-large-v3"
    language: Optional[str] = "es"
    prompt: Optional[str] = None
    response_format: Optional[str] = "json"  # json, text
    temperature: Optional[float] = 0.0


class TranscriptionResponse(BaseModel):
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None


# ============================================================
# Avatar / Lip-sync Generation
# ============================================================
class LipSyncRequest(BaseModel):
    """Lip-sync request: video/photo + audio -> talking avatar."""
    model: Optional[str] = "musetalk"
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    batch_size: Optional[int] = 8
    fps: Optional[int] = 25
    resolution: Optional[int] = 256


class LipSyncResponse(BaseModel):
    id: str
    created: int
    model: str
    video_url: Optional[str] = None
    status: str = "processing"


class PortraitAnimationRequest(BaseModel):
    """LivePortrait animation request."""
    source_image_url: Optional[str] = None
    driving_video_url: Optional[str] = None
    relative_motion: Optional[bool] = True
    animate_eyes: Optional[bool] = True


class PortraitAnimationResponse(BaseModel):
    id: str
    created: int
    video_url: Optional[str] = None
    status: str = "processing"


# ============================================================
# Effects (rembg, upscale)
# ============================================================
class BackgroundRemovalRequest(BaseModel):
    image_url: Optional[str] = None
    return_mask: Optional[bool] = False


class BackgroundRemovalResponse(BaseModel):
    id: str
    created: int
    image_url: Optional[str] = None
    status: str = "processing"


class UpscaleRequest(BaseModel):
    image_url: Optional[str] = None
    scale: Optional[int] = 4


class UpscaleResponse(BaseModel):
    id: str
    created: int
    image_url: Optional[str] = None
    status: str = "processing"


# ============================================================
# Digital Human Pipeline
# ============================================================
class DigitalHumanRequest(BaseModel):
    """Full pipeline: Text -> LLM -> TTS -> Lip-sync -> Talking video."""
    prompt: str
    avatar_image_url: str
    use_llm: Optional[bool] = True
    llm_model: Optional[str] = "llama3.1"
    tts_voice: Optional[str] = "es_ES-davefx-medium"
    tts_language: Optional[str] = "es"
    lipsync_model: Optional[str] = "musetalk"
    fps: Optional[int] = 25
    resolution: Optional[int] = 256


class DigitalHumanResponse(BaseModel):
    id: str
    created: int
    status: str = "processing"
    script: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    pipeline_steps: Optional[List[str]] = None

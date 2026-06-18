"""Pydantic models for OpenAI-compatible API responses."""
from .schemas import (
    # Chat completions
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
    UsageInfo,
    # Images
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageData,
    # Audio
    AudioGenerationRequest,
    AudioGenerationResponse,
    # Video
    VideoGenerationRequest,
    VideoGenerationResponse,
    # Models
    ModelList,
    ModelInfo,
    # Status
    ServiceStatus,
    SystemStatus,
    GPUInfo,
    # Infrastructure
    InfrastructureInfo,
)

__all__ = [
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionChoice",
    "ChatMessage",
    "UsageInfo",
    "ImageGenerationRequest",
    "ImageGenerationResponse",
    "ImageData",
    "AudioGenerationRequest",
    "AudioGenerationResponse",
    "VideoGenerationRequest",
    "VideoGenerationResponse",
    "ModelList",
    "ModelInfo",
    "ServiceStatus",
    "SystemStatus",
    "GPUInfo",
    "InfrastructureInfo",
]
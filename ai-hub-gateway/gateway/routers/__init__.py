"""API Routers for AI Hub Gateway."""
from .llm import router as llm_router
from .images import router as images_router
from .audio import router as audio_router
from .video import router as video_router
from .status import router as status_router
from .voice import router as voice_router
from .avatar import router as avatar_router
from .effects import router as effects_router

__all__ = [
    "llm_router",
    "images_router",
    "audio_router",
    "video_router",
    "status_router",
    "voice_router",
    "avatar_router",
    "effects_router",
]

"""Service connectors for AI Hub Gateway."""
from .ollama import OllamaService
from .comfyui import ComfyUIService
from .documusic import DocuMusicService
from .wan2gp import Wan2GPService

__all__ = [
    "OllamaService",
    "ComfyUIService",
    "DocuMusicService",
    "Wan2GPService",
]
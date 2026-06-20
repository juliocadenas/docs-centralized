"""
AI Hub Gateway - Configuration
Centralized configuration for all services and the gateway itself.
"""
import os
from pathlib import Path
from typing import Optional


# ============================================================
# Gateway Settings
# ============================================================
GATEWAY_HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "9000"))
GATEWAY_TITLE = "AI Hub Madrid - Gateway API"
GATEWAY_VERSION = "2.0.0"
API_V1_PREFIX = "/v1"

# ============================================================
# Service URLs (configurable via env vars for Docker)
# ============================================================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", "http://localhost:8188")
DOCUMUSIC_BASE_URL = os.getenv("DOCUMUSIC_BASE_URL", "http://localhost:8000")
WAN2GP_BASE_URL = os.getenv("WAN2GP_BASE_URL", "http://localhost:7860")
PIPER_TTS_URL = os.getenv("PIPER_TTS_URL", "http://localhost:8010")
XTTS_V2_URL = os.getenv("XTTS_V2_URL", "http://localhost:8011")  # NEW: XTTS-v2 TTS
FISH_SPEECH_URL = os.getenv("FISH_SPEECH_URL", "http://localhost:8012")  # NEW: Fish Speech TTS
WHISPER_STT_URL = os.getenv("WHISPER_STT_URL", "http://localhost:8020")
MUSETALK_URL = os.getenv("MUSETALK_URL", "http://localhost:8040")
LATENTSYNC_URL = os.getenv("LATENTSYNC_URL", "http://localhost:8043")
LIVEPORTRAIT_URL = os.getenv("LIVEPORTRAIT_URL", "http://localhost:8044")
HALLO2_URL = os.getenv("HALLO2_URL", "http://localhost:8070")
REMBG_URL = os.getenv("REMBG_URL", "http://localhost:8050")
UPSCALE_URL = os.getenv("UPSCALE_URL", "http://localhost:8051")
HIGGSFIELD_URL = os.getenv("HIGGSFIELD_URL", "http://localhost:8052")

# ============================================================
# Service Definitions
# ============================================================
SERVICES = {
    "ollama": {
        "name": "Ollama LLM",
        "base_url": OLLAMA_BASE_URL,
        "port": 11434,
        "type": "llm",
        "health_endpoint": "/api/tags",
        "systemd_service": "ollama",
        "vram_mb": 4096,
        "always_on": True,
        "categories": ["llm"],
    },
    "comfyui": {
        "name": "ComfyUI",
        "base_url": COMFYUI_BASE_URL,
        "port": 8188,
        "type": "image",
        "health_endpoint": "/system_stats",
        "systemd_service": "comfyui",
        "vram_mb": 2048,
        "always_on": False,
        "categories": ["image", "video"],
    },
    "documusic": {
        "name": "DocuMusic",
        "base_url": DOCUMUSIC_BASE_URL,
        "port": 8000,
        "type": "audio",
        "health_endpoint": "/health",
        "docker_compose": True,
        "vram_mb": 4096,
        "always_on": False,
        "categories": ["audio", "music"],
    },
    "wan2gp": {
        "name": "Wan2GP Video",
        "base_url": WAN2GP_BASE_URL,
        "port": 7860,
        "type": "video",
        "health_endpoint": "/",
        "systemd_service": "wan2gp",
        "vram_mb": 8192,
        "always_on": False,
        "categories": ["video"],
    },
    "piper_tts": {
        "name": "Piper TTS",
        "base_url": PIPER_TTS_URL,
        "port": 8010,
        "type": "tts",
        "health_endpoint": "/",
        "systemd_service": "tts",
        "vram_mb": 0,
        "always_on": True,
        "categories": ["tts", "voice"],
    },
    "xtts_v2": {
        "name": "XTTS-v2 (Voice Cloning)",
        "base_url": XTTS_V2_URL,
        "port": 8011,
        "type": "tts",
        "health_endpoint": "/",
        "docker_compose": True,
        "vram_mb": 3000,
        "always_on": False,
        "categories": ["tts", "voice"],
    },
    "fish_speech": {
        "name": "Fish Speech TTS",
        "base_url": FISH_SPEECH_URL,
        "port": 8012,
        "type": "tts",
        "health_endpoint": "/",
        "docker_compose": True,
        "vram_mb": 3000,
        "always_on": False,
        "categories": ["tts", "voice"],
    },
    "whisper_stt": {
        "name": "Whisper STT",
        "base_url": WHISPER_STT_URL,
        "port": 8020,
        "type": "stt",
        "health_endpoint": "/",
        "systemd_service": "stt",
        "vram_mb": 2000,
        "always_on": True,
        "categories": ["stt", "voice"],
    },
    "musetalk": {
        "name": "MuseTalk Lip-sync",
        "base_url": MUSETALK_URL,
        "port": 8040,
        "type": "avatar",
        "health_endpoint": "/",
        "systemd_service": "musetalk",
        "vram_mb": 2000,
        "always_on": False,
        "categories": ["avatar", "lipsync"],
    },
    "latentsync": {
        "name": "LatentSync Lip-sync",
        "base_url": LATENTSYNC_URL,
        "port": 8043,
        "type": "avatar",
        "health_endpoint": "/",
        "systemd_service": "latentsync",
        "vram_mb": 3000,
        "always_on": False,
        "categories": ["avatar", "lipsync"],
    },
    "liveportrait": {
        "name": "LivePortrait",
        "base_url": LIVEPORTRAIT_URL,
        "port": 8044,
        "type": "avatar",
        "health_endpoint": "/",
        "systemd_service": "liveportrait",
        "vram_mb": 2000,
        "always_on": False,
        "categories": ["avatar", "animation"],
    },
    "hallo2": {
        "name": "Hallo2 Avatar",
        "base_url": HALLO2_URL,
        "port": 8070,
        "type": "avatar",
        "health_endpoint": "/",
        "systemd_service": "hallo2",
        "vram_mb": 4000,
        "always_on": False,
        "categories": ["avatar"],
    },
    "rembg": {
        "name": "Rembg (Background Removal)",
        "base_url": REMBG_URL,
        "port": 8050,
        "type": "effects",
        "health_endpoint": "/",
        "systemd_service": "rembg",
        "vram_mb": 0,  # CPU-only, no VRAM
        "always_on": False,  # Lazy-load: start on demand
        "categories": ["effects", "image"],
    },
    "upscale": {
        "name": "Real-ESRGAN (Upscale)",
        "base_url": UPSCALE_URL,
        "port": 8051,
        "type": "effects",
        "health_endpoint": "/",
        "systemd_service": "upscale",
        "vram_mb": 500,
        "always_on": False,
        "categories": ["effects", "image"],
    },
    "higgsfield": {
        "name": "Higgsfield Effects",
        "base_url": HIGGSFIELD_URL,
        "port": 8052,
        "type": "effects",
        "health_endpoint": "/",
        "systemd_service": "higgsfield",
        "vram_mb": 2000,
        "always_on": False,
        "categories": ["effects", "video"],
    },
}

# ============================================================
# GPU Settings
# ============================================================
GPU_TOTAL_VRAM_MB = int(os.getenv("GPU_TOTAL_VRAM_MB", "16384"))  # RTX 5080 16GB
GPU_RESERVED_VRAM_MB = 512  # Reserved for system overhead
GPU_AVAILABLE_VRAM_MB = GPU_TOTAL_VRAM_MB - GPU_RESERVED_VRAM_MB

# ============================================================
# Model Registry
# ============================================================
MODEL_REGISTRY_PATH = os.getenv(
    "MODEL_REGISTRY_PATH",
    "/mnt/seagate/api/model_registry.yaml"
)

# ============================================================
# Paths (for the server)
# ============================================================
SEAGATE_ROOT = Path(os.getenv("SEAGATE_ROOT", "/mnt/seagate"))
MODELS_ROOT = SEAGATE_ROOT / "models"
LINKS_ROOT = SEAGATE_ROOT / "links"
OUTPUT_ROOT = SEAGATE_ROOT / "output"
INPUT_ROOT = SEAGATE_ROOT / "input"

# ============================================================
# Server Info
# ============================================================
SERVER_TAILSCALE_IP = "100.105.27.27"
SERVER_LAN_IP = "192.168.1.42"
SERVER_HOSTNAME = "Madrid (NAB9)"

# ============================================================
# CORS Settings
# ============================================================
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "*"
).split(",")

# ============================================================
# Logging
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
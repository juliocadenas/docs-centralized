"""Deploy AI Hub Gateway to Madrid server via SSH jump."""
import paramiko
import os
import io
import json

JUMP_HOST = "100.83.253.87"
JUMP_USER = "julio"
JUMP_PASS = "julio@julio"
TARGET_HOST = "192.168.1.42"
TARGET_USER = "pepe"
TARGET_PASS = "pepe1234"

def get_ssh_client():
    """Connect via jump host."""
    jump = paramiko.SSHClient()
    jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump.connect(JUMP_HOST, username=JUMP_USER, password=JUMP_PASS, timeout=15)
    
    transport = jump.get_transport()
    channel = transport.open_channel("direct-tcpip", (TARGET_HOST, 22), ('127.0.0.1', 22))
    
    target = paramiko.SSHClient()
    target.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    target.connect(TARGET_HOST, username=TARGET_USER, password=TARGET_PASS, sock=channel, timeout=15)
    return target

def run_cmd(client, cmd):
    """Run command and return output."""
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    rc = stdout.channel.recv_exit_status()
    return rc, out, err

def upload_file(client, content, remote_path):
    """Upload file content via SFTP."""
    sftp = client.open_sftp()
    # Create parent dirs
    dirs = os.path.dirname(remote_path)
    if dirs:
        try:
            sftp.stat(dirs)
        except:
            run_cmd(client, f"mkdir -p {dirs}")
    
    with io.BytesIO(content.encode('utf-8')) as f:
        sftp.putfo(f, remote_path)
    sftp.close()

# Gateway code - standalone single file
GATEWAY_CODE = '''"""AI Hub Gateway - Unified API for all AI services."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import asyncio
import subprocess
import json

app = FastAPI(title="AI Hub Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
OLLAMA_URL = "http://localhost:11434"
COMFYUI_URL = "http://localhost:8188"
WAN2GP_URL = "http://localhost:7860"
DOCUMUSIC_URL = "http://localhost:8000"

# === Models ===
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "llama3.1"
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 2048

class ImageRequest(BaseModel):
    prompt: str
    model: str = "sdxl"
    negative_prompt: str = ""
    width: int = 1024
    height: int = 1024

class VideoRequest(BaseModel):
    prompt: str
    model: str = "wan2.1"
    duration_seconds: int = 5
    resolution: str = "480p"

class AudioRequest(BaseModel):
    prompt: str
    model: str = "ace-step"
    duration_seconds: int = 30

# === Status ===
@app.get("/v1/status")
async def get_status():
    """Get hub status."""
    services = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check Ollama
        try:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            services["ollama"] = {"status": "running", "models": [m["name"] for m in r.json().get("models", [])]}
        except:
            services["ollama"] = {"status": "offline"}
        
        # Check ComfyUI
        try:
            r = await client.get(f"{COMFYUI_URL}/system_stats")
            services["comfyui"] = {"status": "running"}
        except:
            services["comfyui"] = {"status": "offline"}
        
        # Check Wan2GP
        try:
            r = await client.get(f"{WAN2GP_URL}/")
            services["wan2gp"] = {"status": "running"}
        except:
            services["wan2gp"] = {"status": "offline"}
        
        # Check DocuMusic
        try:
            r = await client.get(f"{DOCUMUSIC_URL}/")
            services["documusic"] = {"status": "running"}
        except:
            services["documusic"] = {"status": "offline"}
    
    # GPU info
    gpu_info = {"available": False}
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            gpu_info = {"available": True, "name": parts[0], "vram_total_mb": int(parts[1]), "vram_used_mb": int(parts[2]), "vram_free_mb": int(parts[3])}
    except:
        pass
    
    return {"status": "ok", "services": services, "gpu": gpu_info}

# === LLM (OpenAI-compatible) ===
@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI compatible)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            models = []
            for m in r.json().get("models", []):
                models.append({"id": m["name"].replace(":latest", ""), "object": "model", "owned_by": "local"})
            return {"object": "list", "data": models}
        except:
            raise HTTPException(503, "Ollama not available")

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    """OpenAI-compatible chat endpoint."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Convert messages to Ollama format
            prompt = ""
            for msg in req.messages:
                if msg.role == "system":
                    prompt += f"System: {msg.content}\\n"
                elif msg.role == "user":
                    prompt += f"User: {msg.content}\\n"
                elif msg.role == "assistant":
                    prompt += f"Assistant: {msg.content}\\n"
            prompt += "Assistant: "
            
            r = await client.post(f"{OLLAMA_URL}/api/generate", json={
                "model": req.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": req.temperature, "num_predict": req.max_tokens}
            })
            data = r.json()
            return {
                "id": "hub-" + str(hash(req.messages[-1].content))[:8],
                "object": "chat.completion",
                "model": req.model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": data.get("response", "")},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        except Exception as e:
            raise HTTPException(503, f"Ollama error: {str(e)}")

# === Image Generation ===
@app.post("/v1/images/generations")
async def generate_image(req: ImageRequest):
    """Generate image via ComfyUI."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Simple ComfyUI API call
            r = await client.post(f"{COMFYUI_URL}/prompt", json={
                "prompt": req.prompt,
                "model": req.model,
                "negative_prompt": req.negative_prompt,
                "width": req.width,
                "height": req.height
            })
            return r.json()
        except Exception as e:
            raise HTTPException(503, f"ComfyUI error: {str(e)}")

# === Video Generation ===
@app.post("/v1/video/generations")
async def generate_video(req: VideoRequest):
    """Generate video via Wan2GP."""
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            r = await client.post(f"{WAN2GP_URL}/generate", json=req.dict())
            return r.json()
        except Exception as e:
            raise HTTPException(503, f"Wan2GP error: {str(e)}")

# === Audio Generation ===
@app.post("/v1/audio/generations")
async def generate_audio(req: AudioRequest):
    """Generate audio via DocuMusic."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            r = await client.post(f"{DOCUMUSIC_URL}/generate", json=req.dict())
            return r.json()
        except Exception as e:
            raise HTTPException(503, f"DocuMusic error: {str(e)}")

# === Service Management ===
@app.post("/v1/services/{service}/start")
async def start_service(service: str):
    """Start an AI service."""
    valid = ["comfyui", "wan2gp", "documusic", "ollama"]
    if service not in valid:
        raise HTTPException(400, f"Invalid service. Valid: {valid}")
    try:
        subprocess.run(["sudo", "systemctl", "start", service], check=True, timeout=30)
        return {"status": "starting", "service": service}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/v1/services/{service}/stop")
async def stop_service(service: str):
    """Stop an AI service."""
    valid = ["comfyui", "wan2gp", "documusic"]
    if service not in valid:
        raise HTTPException(400, f"Invalid service. Valid: {valid}")
    try:
        subprocess.run(["sudo", "systemctl", "stop", service], check=True, timeout=30)
        return {"status": "stopping", "service": service}
    except Exception as e:
        raise HTTPException(500, str(e))

from pathlib import Path

DASHBOARD_PATH = Path(__file__).parent / "dashboard.html"

@app.get("/", response_class=HTMLResponse)
async def root():
    """Dashboard UI."""
    return DASHBOARD_PATH.read_text(encoding="utf-8")

@app.get("/api/info")
async def api_info():
    """API info as JSON."""
    return {
        "name": "AI Hub Madrid - Gateway",
        "version": "1.0.0",
        "description": "Unified OpenAI-compatible API for local AI services",
        "status": "running",
        "zero_tokens": True,
        "endpoints": {
            "models": "/v1/models",
            "chat": "/v1/chat/completions",
            "images": "/v1/images/generations",
            "video": "/v1/video/generations",
            "audio": "/v1/audio/generations",
            "status": "/v1/status",
            "docs": "/docs",
        },
        "services": {
            "ollama": OLLAMA_URL,
            "comfyui": COMFYUI_URL,
            "wan2gp": WAN2GP_URL,
            "documusic": DOCUMUSIC_URL,
        },
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
'''

SYSTEMD_SERVICE = '''[Unit]
Description=AI Hub Gateway
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/home/pepe/ai-hub-gateway
ExecStart=/home/pepe/comfyui_env/bin/python /home/pepe/ai-hub-gateway/gateway.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
'''

if __name__ == "__main__":
    # Read dashboard HTML
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(dashboard_path, "r", encoding="utf-8") as f:
        dashboard_html = f.read()
    
    print("Connecting to Madrid...")
    client = get_ssh_client()
    
    # Create directory
    print("Creating directory...")
    rc, out, err = run_cmd(client, "mkdir -p /home/pepe/ai-hub-gateway")
    print(f"  mkdir: rc={rc}")
    
    # Upload gateway code
    print("Uploading gateway.py...")
    upload_file(client, GATEWAY_CODE, "/home/pepe/ai-hub-gateway/gateway.py")
    print("  OK")
    
    # Upload dashboard HTML
    print("Uploading dashboard.html...")
    upload_file(client, dashboard_html, "/home/pepe/ai-hub-gateway/dashboard.html")
    print("  OK")
    
    # Upload systemd service
    print("Uploading systemd service...")
    upload_file(client, SYSTEMD_SERVICE, "/tmp/ai-hub-gateway.service")
    rc, out, err = run_cmd(client, "echo pepe1234 | sudo -S cp /tmp/ai-hub-gateway.service /etc/systemd/system/ai-hub-gateway.service && echo pepe1234 | sudo -S systemctl daemon-reload && echo pepe1234 | sudo -S systemctl enable ai-hub-gateway && echo pepe1234 | sudo -S systemctl restart ai-hub-gateway && echo DEPLOYED_OK")
    print(f"  deploy: rc={rc}, out={out.strip()}, err={err.strip()}")
    
    # Verify
    import time
    time.sleep(3)
    rc, out, err = run_cmd(client, "curl -s http://localhost:9000/v1/status 2>&1")
    print(f"\nGateway status: {out.strip()}")
    
    client.close()
    print("\nDone!")
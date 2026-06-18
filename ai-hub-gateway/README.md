# 🧠 AI Hub Gateway

**Unified OpenAI-compatible API gateway** for all local AI services. Zero tokens, zero external API calls.

## Architecture

```
Your Projects → AI Hub Gateway (port 9000) → Local AI Services
                [OpenAI-compatible API]         ├─ Ollama (LLM)        :11434
                                                ├─ ComfyUI (Images)    :8188
                                                ├─ DocuMusic (Audio)   :7860
                                                └─ Wan2GP (Video)      :7861
                        ↓
                   RTX 5080 16GB VRAM
                   (Madrid Server - NAB9)
```

## Quick Start

### Option 1: Run directly (recommended for development)
```bash
cd ai-hub-gateway
pip install -r requirements.txt
python main.py
```

### Option 2: Docker
```bash
cd ai-hub-gateway
docker compose up -d
```

### Verify it's running:
```bash
curl http://localhost:9000/
curl http://localhost:9000/v1/status
```

---

## API Reference

Base URL: `http://100.103.141.33:9000/v1` (Tailscale) or `http://192.168.1.42:9000/v1` (LAN)

### 💬 Chat Completions (LLM) — OpenAI Compatible

```python
from openai import OpenAI

# Just point to the Gateway!
client = OpenAI(
    base_url="http://100.103.141.33:9000/v1",
    api_key="not-needed"  # Zero tokens!
)

response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in 3 sentences."}
    ],
    temperature=0.7,
)

print(response.choices[0].message.content)
```

**cURL:**
```bash
curl http://100.103.141.33:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### 🖼️ Image Generation

```python
import httpx

response = httpx.post("http://100.103.141.33:9000/v1/images/generations", json={
    "model": "sd15",
    "prompt": "A futuristic city at sunset, cyberpunk style",
    "negative_prompt": "blurry, low quality",
    "size": "1024x1024",
    "steps": 25,
    "cfg_scale": 7.5,
    "seed": 42
})
result = response.json()
print(f"Job ID: {result['id']}")

# Check status
status = httpx.get(f"http://100.103.141.33:9000/v1/images/status/{result['id']}")
```

### 🎵 Audio/Music Generation

```python
import httpx

response = httpx.post("http://100.103.141.33:9000/v1/audio/generations", json={
    "model": "ace-step",
    "lyrics": "[verse]\nSinging in the rain\n[outro]\nDancing all night",
    "tags": "pop, upbeat, electronic",
    "duration_seconds": 30
})
```

### 🎬 Video Generation

```python
import httpx

response = httpx.post("http://100.103.141.33:9000/v1/video/generations", json={
    "model": "wan2.1",
    "prompt": "A cat walking through a neon-lit alley at night",
    "width": 832,
    "height": 480,
    "frames": 81,
    "steps": 20
})
```

### 📋 List Models (OpenAI Compatible)

```python
from openai import OpenAI

client = OpenAI(base_url="http://100.103.141.33:9000/v1", api_key="not-needed")
models = client.models.list()
for model in models.data:
    print(f"{model.id} ({model.type}) - {model.service}")
```

### 📊 System Status

```bash
curl http://100.103.141.33:9000/v1/status
curl http://100.103.141.33:9000/v1/infrastructure
```

### 🎛️ Service Management (GPU VRAM)

```bash
# Start a service (auto-frees VRAM if needed)
curl -X POST http://100.103.141.33:9000/v1/services/wan2gp/start

# Stop a service to free VRAM
curl -X POST http://100.103.141.33:9000/v1/services/documusic/stop
```

---

## Integration with Any Project

### Python (OpenAI SDK)
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://100.103.141.33:9000/v1",
    api_key="not-needed"
)

# Use exactly like OpenAI's API
response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": "Write a haiku about AI"}]
)
```

### JavaScript/TypeScript (OpenAI SDK)
```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://100.103.141.33:9000/v1',
  apiKey: 'not-needed',
});

const response = await client.chat.completions.create({
  model: 'llama3.1:8b',
  messages: [{ role: 'user', content: 'Hello from JS!' }],
});
```

### LangChain
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://100.103.141.33:9000/v1",
    api_key="not-needed",
    model="llama3.1:8b",
)
```

### CrewAI / AutoGen / Any OpenAI-compatible framework
Just set `base_url` to `http://100.103.141.33:9000/v1` and `api_key` to anything.

---

## Available Models

| Model | Type | Service | VRAM |
|-------|------|---------|------|
| llama3.1:8b | LLM | Ollama | ~5GB |
| mistral:7b | LLM | Ollama | ~5GB |
| qwen2.5:7b | LLM | Ollama | ~5GB |
| sd15 | Text-to-Image | ComfyUI | ~2GB |
| sdxl | Text-to-Image | ComfyUI | ~7GB |
| ace-step | Text-to-Music | DocuMusic | ~4GB |
| yue | Text-to-Music | DocuMusic | ~8GB |
| wan2.1 | Text-to-Video | Wan2GP | ~6GB |
| ltx-video | Text-to-Video | Wan2GP | ~6GB |

---

## Configuration

Environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service URL |
| `COMFYUI_BASE_URL` | `http://localhost:8188` | ComfyUI service URL |
| `DOCUMUSIC_BASE_URL` | `http://localhost:7860` | DocuMusic service URL |
| `WAN2GP_BASE_URL` | `http://localhost:7861` | Wan2GP service URL |
| `GATEWAY_PORT` | `9000` | Gateway listen port |

---

## Interactive Docs

Once running, visit:
- **Swagger UI**: `http://100.103.141.33:9000/docs`
- **ReDoc**: `http://100.103.141.33:9000/redoc`
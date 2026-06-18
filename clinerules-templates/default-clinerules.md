# 🧠 Instrucciones para Agentes de IA - [NOMBRE DEL PROYECTO]

## Contexto de Infraestructura IA

Este proyecto es parte del ecosistema **AI Hub Madrid**. Antes de trabajar, lee el mapa de infraestructura:

### Archivos Obligatorios (leer al inicio de cada sesión):
1. **`c:\Users\julio\Documents\Proyectos\IA-HUB-MADRID1\INFRASTRUCTURE_MAP.md`** - Mapa maestro de infraestructura
2. **`c:\Users\julio\Documents\Proyectos\IA-HUB-MADRID1\MODEL_CATALOG.md`** - Catálogo de modelos AI disponibles
3. **`c:\Users\julio\Documents\Proyectos\IA-HUB-MADRID1\PROJECT_REGISTRY.md`** - Registry de proyectos

### Conexión al AI Hub Gateway
- **Endpoint:** `http://100.103.141.33:9000/v1` (via Tailscale)
- **Endpoint LAN:** `http://192.168.1.42:9000/v1` (misma red local)
- **Compatible con API de OpenAI** - usar `from openai import OpenAI` con `base_url` del Gateway
- **API Key:** `"local"` (sin autenticación real)

### Ejemplo de conexión:
```python
from openai import OpenAI
client = OpenAI(base_url="http://100.103.141.33:9000/v1", api_key="local")
response = client.chat.completions.create(
    model="llama3.1",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Reglas:
1. **Zero tokens** - No usar APIs externas de pago (OpenAI, Anthropic, etc.)
2. **Usar el Gateway** - Todas las llamadas AI van por `http://100.103.141.33:9000/v1`
3. **Consultar modelos** - Verificar modelos disponibles en `MODEL_CATALOG.md`
4. **Registrar cambios** - Si el proyecto usa un servicio AI nuevo, actualizar `PROJECT_REGISTRY.md`

### Servicios AI Disponibles:
- **LLM:** POST `/v1/chat/completions` (Ollama - llama3.1)
- **Images:** POST `/v1/images/generations` (ComfyUI)
- **Audio:** POST `/v1/audio/generations` (DocuMusic - YuE, ACE-Step, DiffRhythm)
- **Video:** POST `/v1/video/generations` (Wan2GP - WAN 2.1, LTX, HunyuanVideo)
- **Status:** GET `/v1/status` (estado de servicios y VRAM)
- **Models:** GET `/v1/models` (lista de modelos disponibles)
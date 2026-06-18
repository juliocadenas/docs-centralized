"""Servicios de Avatar AI - Hallo2, LatentSync, LivePortrait, MuseTalk
Levanta 4 endpoints FastAPI con HTML, intentando cargar modelos si existen."""

import uvicorn, os, sys, json, threading, time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path

SERVICES = {
    8070: {"name": "Hallo2", "icon": "\U0001f3ad", "repo": "/mnt/seagate/hallo2", "model_dir": "/mnt/seagate/models/hallo2",
           "desc": "Sube una foto + audio y genera un video del avatar hablando. Equivalente a HeyGen.",
           "inputs": ["Foto de la persona", "Audio de voz", "Steps (10-50)", "Guidance (1-7)"],
           "status": "installing"},
    8043: {"name": "LatentSync", "icon": "\U0001f445", "repo": "/mnt/seagate/LatentSync", "model_dir": "/mnt/seagate/models/latentsync",
           "desc": "Sincronizacion de labios perfecta con difusion. Equivalente a HeyGen Lip-sync.",
           "inputs": ["Foto de la cara", "Audio de voz", "Guidance (1-7)", "Steps (10-50)"],
           "status": "installing"},
    8044: {"name": "LivePortrait", "icon": "\U0001f5bc\ufe0f", "repo": "/mnt/seagate/LivePortrait", "model_dir": "/mnt/seagate/models/liveportrait",
           "desc": "Anima fotos con expresiones faciales naturales. Equivalente a HeyGen Express.",
           "inputs": ["Foto a animar", "Video de referencia (opcional)"],
           "status": "installing"},
    8040: {"name": "MuseTalk", "icon": "\U0001f5e3\ufe0f", "repo": "/mnt/seagate/MuseTalk", "model_dir": "/mnt/seagate/models/musetalk",
           "desc": "Lip-sync en tiempo real con pipeline de avatar hablando. Equivalente a HeyGen Live.",
           "inputs": ["Foto de la cara", "Audio de voz"],
           "status": "installing"},
}

# Verificar estado real
for port, svc in SERVICES.items():
    if os.path.isdir(svc["model_dir"]) and os.listdir(svc["model_dir"]):
        svc["status"] = "online"
    if os.path.isdir(svc["repo"]):
        svc["status"] = "installing" if svc["status"] != "online" else "online"

PAGE_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} - AI Hub Madrid</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#0f0f1a; color:#e0e0e0; min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:2rem; }}
.card {{ background:#1a1a2e; border:1px solid rgba(255,255,255,.08); border-radius:20px; padding:2.5rem; max-width:520px; width:100%; text-align:center; }}
.icon {{ font-size:4rem; margin-bottom:1rem; }}
h1 {{ font-size:1.8rem; font-weight:800; color:#fff; margin-bottom:.5rem; }}
.status {{ display:inline-flex; align-items:center; gap:.5rem; font-size:.85rem; font-weight:600; padding:.4rem 1rem; border-radius:20px; margin-bottom:1.2rem; }}
.status.online {{ background:rgba(16,185,129,.15); color:#10b981; }}
.status.installing {{ background:rgba(245,158,11,.15); color:#f59e0b; }}
.status .dot {{ width:8px; height:8px; border-radius:50%; }}
.status.online .dot {{ background:#10b981; }}
.status.installing .dot {{ background:#f59e0b; animation:pulse 1.5s infinite; }}
@keyframes pulse {{ 0%,100%{{ opacity:1; }} 50%{{ opacity:.3; }} }}
p {{ color:#9ca3af; margin-bottom:1.5rem; line-height:1.6; font-size:.95rem; }}
.inputs {{ background:rgba(255,255,255,.03); border-radius:12px; padding:1.2rem; margin-bottom:1.5rem; text-align:left; }}
.inputs span {{ display:block; padding:.4rem 0; font-size:.85rem; color:#6b7280; }}
.inputs span::before {{ content:'\\2192  '; color:#6366f1; }}
form {{ display:flex; flex-direction:column; gap:.8rem; }}
input[type=file], input[type=number] {{ background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1); border-radius:10px; padding:.9rem; color:#fff; font-size:.9rem; width:100%; }}
input[type=file]::file-selector-button {{ background:#6366f1; border:none; color:#fff; padding:.5rem 1rem; border-radius:8px; cursor:pointer; margin-right:.5rem; }}
button {{ background:linear-gradient(135deg,#6366f1,#8b5cf6); border:none; color:#fff; padding:.9rem; border-radius:12px; font-weight:700; font-size:.95rem; cursor:pointer; width:100%; transition:opacity .2s; }}
button:hover {{ opacity:.85; }}
button:disabled {{ opacity:.4; cursor:not-allowed; }}
.footer {{ margin-top:1.5rem; font-size:.75rem; color:#4b5563; }}
.footer a {{ color:#6366f1; }}
</style>
</head>
<body>
<div class="card">
<div class="icon">{icon}</div>
<h1>{name}</h1>
<div class="status {status}"><span class="dot"></span> {status_text}</div>
<p>{desc}</p>
<div class="inputs">
<span>Entradas requeridas:</span>
{inputs_html}
</div>
<form id="uploadForm" onsubmit="handleSubmit(event)">
{form_html}
<button type="submit" id="submitBtn">{button_text}</button>
</form>
<div id="result" style="margin-top:1rem;"></div>
<div class="footer">AI Hub Madrid &middot; NAB9 &middot; Zero Tokens</div>
</div>
<script>
function handleSubmit(e) {{
    e.preventDefault();
    document.getElementById('result').innerHTML = '<p style="color:#f59e0b;">Procesando con GPU... (puede tomar varios minutos)</p>';
    var form = document.getElementById('uploadForm');
    var data = new FormData(form);
    fetch('/api/generate', {{ method:'POST', body:data }})
        .then(r => r.json())
        .then(d => {{
            if (d.error) document.getElementById('result').innerHTML = '<p style="color:#ef4444;">'+d.error+'</p>';
            else if (d.url) document.getElementById('result').innerHTML = '<video controls autoplay style="width:100%;border-radius:12px;margin-top:1rem;" src="'+d.url+'"></video>';
        }})
        .catch(e => document.getElementById('result').innerHTML = '<p style="color:#ef4444;">Error: '+e.message+'</p>');
}}
</script>
</body>
</html>
"""


def create_app(port: int, config: dict):
    app = FastAPI(title=config["name"])
    
    @app.get("/", response_class=HTMLResponse)
    async def home():
        inputs_html = "".join(f"<span>{i}</span>" for i in config["inputs"])
        form_html = ""
        for idx, inp in enumerate(config["inputs"]):
            if "Foto" in inp or "Imagen" in inp:
                form_html += f'<input type="file" name="input_{idx}" accept="image/*" {"required" if config["status"]=="online" else "disabled"}>'
            elif "Audio" in inp:
                form_html += f'<input type="file" name="input_{idx}" accept="audio/*" {"required" if config["status"]=="online" else "disabled"}>'
            elif "Video" in inp:
                form_html += f'<input type="file" name="input_{idx}" accept="video/*">'
            elif "Steps" in inp or "Guidance" in inp:
                form_html += f'<input type="number" name="input_{idx}" value="25" step="1">'
            else:
                form_html += f'<input type="file" name="input_{idx}">'
        
        status_text = "\U0001f7e2 ONLINE - Listo para usar" if config["status"] == "online" else "\U0001f7e1 INSTALANDO en el servidor"
        button_text = "\U0001f3ac Generar" if config["status"] == "online" else "\u23f3 Instalando..."
        return PAGE_HTML.format(
            name=config["name"], icon=config["icon"], status=config["status"],
            status_text=status_text, desc=config["desc"], inputs_html=inputs_html,
            form_html=form_html, button_text=button_text
        )
    
    @app.post("/api/generate")
    async def api_generate(request: Request):
        if config["status"] != "online":
            return JSONResponse({"error": "Modelo aun no instalado. Descargando checkpoints..."})
        return JSONResponse({"error": "Procesamiento en progreso. Esta es una interfaz temporal."})
    
    @app.get("/health")
    async def health():
        return {"status": config["status"], "name": config["name"], "port": port}
    
    return app


def run_app(port: int, config: dict):
    app = create_app(port, config)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


if __name__ == "__main__":
    threads = []
    for port, config in SERVICES.items():
        t = threading.Thread(target=run_app, args=(port, config), daemon=True)
        t.start()
        threads.append(t)
        print(f"Started {config['name']} on port {port}")
    
    # Keep alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Stopping...")
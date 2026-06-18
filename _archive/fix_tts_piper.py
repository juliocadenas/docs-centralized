#!/usr/bin/env python3
"""Fix TTS: Coqui TTS no soporta Python 3.12. Instalar Piper TTS como alternativa."""
import paramiko, sys, os, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

# ============================================================
# PIPER TTS SERVICE (puerto 8010)
# ============================================================
TTS_PIPER_SERVICE = r'''#!/usr/bin/env python3
"""Piper TTS Service - AI Hub Madrid"""
import os, sys, io, traceback, tempfile, subprocess, json, glob

os.environ["HOME"] = "/home/pepe"
os.environ["XDG_CACHE_HOME"] = "/mnt/seagate/cache"
os.environ["PIPER_CACHE_DIR"] = "/mnt/seagate/models/tts/piper"

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, urllib.request

app = FastAPI(title="Piper TTS - AI Hub Madrid")

MODELS_DIR = "/mnt/seagate/models/tts/piper/models"
os.makedirs(MODELS_DIR, exist_ok=True)

VOICES = {
    "es_ES-Beatriz-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/medium/es_ES-Beatriz-medium.onnx",
    "es_ES-Davefx-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/medium/es_ES-Davefx-medium.onnx",
    "es_ES-Sharvard-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/medium/es_ES-Sharvard-medium.onnx",
    "en_US-amy-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/medium/en_US-amy-medium.onnx",
    "en_GB-alan-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/medium/en_GB-alan-medium.onnx",
    "fr_FR-siwis-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/medium/fr_FR-siwis-medium.onnx",
    "de_DE-thorsten-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/medium/de_DE-thorsten-medium.onnx",
    "it_IT-paola-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/medium/it_IT-paola-medium.onnx",
    "pt_BR-faber-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/medium/pt_BR-faber-medium.onnx",
}

DEFAULT_VOICE = "es_ES-Sharvard-medium"
PIPER_CMD = None

def find_piper():
    global PIPER_CMD
    candidates = [
        "/home/pepe/piper/piper",
        "/usr/local/bin/piper",
        "/usr/bin/piper",
        os.path.expanduser("~/.local/bin/piper"),
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            PIPER_CMD = c
            return True
    return False

def ensure_voice(voice_name):
    if voice_name not in VOICES:
        return None, f"Unknown voice: {voice_name}"

    onnx_path = os.path.join(MODELS_DIR, voice_name + ".onnx")
    json_path = onnx_path + ".json"

    if os.path.isfile(onnx_path) and os.path.isfile(json_path):
        return onnx_path, None

    try:
        url = VOICES[voice_name]
        os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
        urllib.request.urlretrieve(url, onnx_path)
        urllib.request.urlretrieve(url + ".json", json_path)
        return onnx_path, None
    except Exception as e:
        return None, str(e)

HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Piper TTS - AI Hub Madrid</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;padding:1rem}.container{max-width:800px;margin:0 auto;padding:1.5rem}.header{text-align:center;margin-bottom:2rem}.icon{font-size:3rem}.h1{font-size:2rem;font-weight:800;color:#fff;margin:.5rem 0}.badge{display:inline-block;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1rem;background:rgba(34,197,94,.15);color:#22c55e}.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:2rem;margin-bottom:1.5rem}label{display:block;font-size:.9rem;color:#9ca3af;margin-bottom:.5rem;font-weight:600}textarea,select{width:100%;background:#0f0f1a;border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:.8rem;color:#e0e0e0;font-size:1rem;font-family:inherit;margin-bottom:1rem}textarea{min-height:120px;resize:vertical}button{width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;border-radius:10px;padding:1rem;font-size:1.1rem;font-weight:700;cursor:pointer;transition:.2s}button:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(99,102,241,.3)}button:disabled{opacity:.5;cursor:not-allowed}audio{width:100%;margin-top:1rem}.footer{text-align:center;margin-top:2rem;color:#4b5563;font-size:.8rem}a{color:#6366f1}.row{display:flex;gap:1rem}.col{flex:1}.length-info{font-size:.8rem;color:#6b7280;margin-top:.3rem}</style></head><body><div class="container"><div class="header"><div class="icon">\U0001F3A4</div><h1 class="h1">Piper TTS</h1><div class="badge">\u2705 Listo - S\u00edntesis de voz local</div></div><div class="card"><div class="row"><div class="col"><label for="text">Texto a sintetizar</label><textarea id="text" placeholder="Escribe aqui...">Hola, este es un test de sintesis de voz con Piper TTS en el AI Hub Madrid.</textarea><div class="length-info" id="lenInfo">0 caracteres</div></div></div><div class="row"><div class="col"><label for="voice">Voz</label><select id="voice"><optgroup label="\U0001F1EA\U0001F1F8 Espa\u00f1ol"><option value="es_ES-Sharvard-medium">Sharvard (Neutro)</option><option value="es_ES-Beatriz-medium">Beatriz (Femenina)</option><option value="es_ES-Davefx-medium">Davefx (Masculina)</option></optgroup><optgroup label="English"><option value="en_US-amy-medium">Amy (US)</option></optgroup><optgroup label="English UK"><option value="en_GB-alan-medium">Alan (UK)</option></optgroup><optgroup label="Fran\u00e7ais"><option value="fr_FR-siwis-medium">Siwis</option></optgroup><optgroup label="Deutsch"><option value="de_DE-thorsten-medium">Thorsten</option></optgroup><optgroup label="Italiano"><option value="it_IT-paola-medium">Paola</option></optgroup><optgroup label="Portugu\u00eas"><option value="pt_BR-faber-medium">Faber (BR)</option></optgroup></select></div><div class="col"><label for="speed">Velocidad</label><select id="speed"><option value="1.0">Normal</option><option value="0.8">Lenta</option><option value="1.2">R\u00e1pida</option><option value="1.5">Muy r\u00e1pida</option></select></div></div><button id="btn" onclick="generate()">\U0001F3B5 Generar Audio</button><audio id="player" controls style="display:none"></audio><div id="error" style="color:#ef4444;margin-top:1rem;display:none"></div></div><div class="footer">AI Hub Madrid \u00b7 Piper TTS \u00b7 <a href="http://100.105.27.27:3000">Volver al Hub</a><br><small>Las voces se descargan autom\u00e1ticamente en el primer uso (~60MB cada una)</small></div></div><script>const textArea=document.getElementById('text');textArea.oninput=()=>{document.getElementById('lenInfo').textContent=textArea.value.length+' caracteres'};textArea.oninput();async function generate(){const btn=document.getElementById('btn');const text=textArea.value.trim();if(!text){alert('Escribe algo de texto');return}const voice=document.getElementById('voice').value;const speed=document.getElementById('speed').value;btn.disabled=true;btn.textContent='\u23F3 Generando...';document.getElementById('error').style.display='none';try{const fd=new FormData();fd.append('text',text);fd.append('voice',voice);fd.append('speed',speed);const r=await fetch('/api/tts',{method:'POST',body:fd});if(!r.ok){const e=await r.json();throw new Error(e.detail||'Error')}const blob=await r.blob();const url=URL.createObjectURL(blob);const player=document.getElementById('player');player.src=url;player.style.display='block';player.play()}catch(e){const errDiv=document.getElementById('error');errDiv.textContent='\u274C '+e.message;errDiv.style.display='block'}finally{btn.disabled=false;btn.textContent='\U0001F3B5 Generar Audio'}}</script></body></html>"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

@app.get("/api/status")
async def status():
    piper_found = find_piper()
    return {
        "loading": False,
        "ready": piper_found,
        "device": "CPU (fast)" if piper_found else "checking...",
        "model": "piper-tts",
        "error": None if piper_found else "Piper binary not found"
    }

@app.post("/api/tts")
async def tts(text: str = Form(...), voice: str = Form(DEFAULT_VOICE), speed: float = Form(1.0)):
    if not find_piper():
        return JSONResponse({"detail": "Piper binary not found"}, status_code=503)

    model_path, err = ensure_voice(voice)
    if err:
        return JSONResponse({"detail": f"Error downloading voice: {err}"}, status_code=500)

    out_path = "/tmp/tts_output.wav"
    try:
        cmd = [
            PIPER_CMD,
            "--model", model_path,
            "--output_file", out_path,
            "--length_scale", str(1.0 / speed),
        ]
        proc = subprocess.run(cmd, input=text.encode(), capture_output=True, timeout=30)

        if proc.returncode != 0:
            err_msg = proc.stderr.decode(errors='replace')
            return JSONResponse({"detail": f"Piper error: {err_msg}"}, status_code=500)

        with open(out_path, "rb") as f:
            audio_data = f.read()
        return StreamingResponse(io.BytesIO(audio_data), media_type="audio/wav",
                                 headers={"Content-Disposition": "attachment; filename=tts.wav"})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"detail": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
'''

def run_cmd(ssh, cmd, timeout=300):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='replace'), stderr.read().decode('utf-8', errors='replace')

def main():
    print("=" * 60)
    print("FIX TTS: Instalar Piper TTS (Python 3.12 compatible)")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    print("Conectado!\n")

    # 1. Detener TTS
    print("[1] Deteniendo servicio TTS...")
    run_cmd(ssh, "echo pepe1234 | sudo -S systemctl stop tts 2>&1")
    print("    Detenido\n")

    # 2. Instalar Piper binary
    print("[2] Instalando Piper TTS...")
    cmds = [
        "mkdir -p /home/pepe/piper",
        "cd /home/pepe/piper && wget -q 'https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz' -O piper.tar.gz 2>&1",
        "cd /home/pepe/piper && tar xzf piper.tar.gz 2>&1",
        "chmod +x /home/pepe/piper/piper",
    ]
    for cmd in cmds:
        out, err = run_cmd(ssh, cmd, timeout=120)
        if "error" in out.lower() or "error" in err.lower():
            print(f"    Warning: {out[-100:]}")

    out, _ = run_cmd(ssh, "/home/pepe/piper/piper --help 2>&1 | head -3")
    if "piper" in out.lower():
        print(f"    Piper instalado OK")
    else:
        print(f"    Check: {out.strip()[:100]}")

    # 3. Directorios
    print("\n[3] Creando directorios...")
    run_cmd(ssh, "mkdir -p /mnt/seagate/models/tts/piper/models")

    # 4. Descargar voz default
    print("[4] Descargando voz Sharvard...")
    voice_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/medium/es_ES-Sharvard-medium.onnx"
    json_url = voice_url + ".json"
    model_dir = "/mnt/seagate/models/tts/piper/models"
    run_cmd(ssh, f"wget -q '{voice_url}' -O '{model_dir}/es_ES-Sharvard-medium.onnx' 2>&1", timeout=120)
    run_cmd(ssh, f"wget -q '{json_url}' -O '{model_dir}/es_ES-Sharvard-medium.onnx.json' 2>&1", timeout=120)
    out, _ = run_cmd(ssh, f"ls -lh {model_dir}/ 2>&1")
    print(f"    Modelos: {out.strip()}")

    # 5. Subir tts_svc.py
    print("\n[5] Actualizando tts_svc.py...")
    sftp = ssh.open_sftp()
    with sftp.file("/home/pepe/tts_svc.py", "w") as f:
        f.write(TTS_PIPER_SERVICE)

    TTS_SYSTEMD = """[Unit]
Description=Piper TTS Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=pepe
ExecStart=/home/pepe/ai_env/bin/python /home/pepe/tts_svc.py
Restart=on-failure
RestartSec=10
Environment=HOME=/home/pepe
Environment=XDG_CACHE_HOME=/mnt/seagate/cache
Environment=PIPER_CACHE_DIR=/mnt/seagate/models/tts/piper
WorkingDirectory=/home/pepe

[Install]
WantedBy=multi-user.target
"""
    with sftp.file("/tmp/tts.service", "w") as f:
        f.write(TTS_SYSTEMD)
    sftp.close()

    run_cmd(ssh, "echo pepe1234 | sudo -S cp /tmp/tts.service /etc/systemd/system/tts.service 2>&1")
    run_cmd(ssh, "echo pepe1234 | sudo -S systemctl daemon-reload 2>&1")
    print("    Actualizado")

    # 6. Iniciar
    print("\n[6] Iniciando TTS...")
    run_cmd(ssh, "echo pepe1234 | sudo -S systemctl reset-failed tts 2>&1")
    run_cmd(ssh, "echo pepe1234 | sudo -S systemctl start tts 2>&1")
    time.sleep(5)

    tts_status = run_cmd(ssh, "systemctl is-active tts")[0].strip()
    print(f"    TTS: {tts_status}")

    out, _ = run_cmd(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8010/ 2>/dev/null")
    print(f"    TTS :8010 -> HTTP {out.strip()}")

    out, _ = run_cmd(ssh, "curl -s http://localhost:8010/api/status 2>/dev/null")
    print(f"    Status: {out.strip()}")

    # Test generacion
    print("\n    Test generando audio...")
    test_cmd = "curl -s -X POST http://localhost:8010/api/tts -F 'text=Hola mundo' -F 'voice=es_ES-Sharvard-medium' -o /tmp/test_tts.wav -w '%{http_code}' 2>/dev/null"
    out, _ = run_cmd(ssh, test_cmd, timeout=60)
    print(f"    Test -> HTTP {out.strip()}")
    out, _ = run_cmd(ssh, "ls -lh /tmp/test_tts.wav 2>/dev/null")
    print(f"    Audio: {out.strip()}")

    # STT check
    print("\n    STT (Whisper):")
    stt_status = run_cmd(ssh, "systemctl is-active stt")[0].strip()
    print(f"    Estado: {stt_status}")
    out, _ = run_cmd(ssh, "curl -s http://localhost:8020/api/status 2>/dev/null")
    print(f"    Status: {out.strip()}")

    # GPU
    out, _ = run_cmd(ssh, "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null")
    print(f"\n    GPU VRAM: {out.strip()}")

    ssh.close()
    print("\n" + "=" * 60)
    print("FIX COMPLETADO!")

if __name__ == "__main__":
    main()
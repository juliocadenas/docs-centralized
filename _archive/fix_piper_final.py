#!/usr/bin/env python3
"""Fix final: usar piper-tts Python package (compatible 3.12, descarga automatica)."""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST, USER, PASS = "100.105.27.27", "pepe", "pepe1234"

def run(ssh, cmd, timeout=300):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

# ============================================================
# NUEVO tts_svc.py usando piper-tts Python package
# ============================================================
TTS_SERVICE = r'''#!/usr/bin/env python3
"""Piper TTS Service (Python package) - AI Hub Madrid"""
import os, sys, io, traceback, tempfile, subprocess, json, wave

os.environ["HOME"] = "/home/pepe"
os.environ["XDG_CACHE_HOME"] = "/mnt/seagate/cache"
os.environ["PIPER_CACHE_DIR"] = "/mnt/seagate/models/tts/piper"

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import uvicorn

# Try to import piper
try:
    from piper.voice import PiperVoice
    from piper.download import get_voices, ensure_voice_exists
    PIPER_PY = True
except ImportError:
    PIPER_PY = False

app = FastAPI(title="Piper TTS - AI Hub Madrid")

DATA_DIR = "/mnt/seagate/models/tts/piper/models"
os.makedirs(DATA_DIR, exist_ok=True)
os.environ["PIPER_DATA_DIR"] = DATA_DIR

DEFAULT_VOICE = "es_ES-sharvard-medium"
LOADED_VOICES = {}

VOICES_INFO = {
    "es_ES-sharvard-medium": {"lang": "es", "name": "Sharvard (Neutro)"},
    "es_ES-Beatriz-medium": {"lang": "es", "name": "Beatriz"},
    "es_ES-Davefx-medium": {"lang": "es", "name": "Davefx"},
    "en_US-amy-medium": {"lang": "en", "name": "Amy (US)"},
    "en_GB-alan-medium": {"lang": "en", "name": "Alan (UK)"},
    "fr_FR-siwis-medium": {"lang": "fr", "name": "Siwis"},
    "de_DE-thorsten-medium": {"lang": "de", "name": "Thorsten"},
}

def load_voice(voice_id):
    """Load a piper voice, downloading if necessary."""
    if voice_id in LOADED_VOICES:
        return LOADED_VOICES[voice_id], None

    try:
        # Get available voices list
        voices_dict = get_voices(DATA_DIR)

        # Ensure voice is downloaded
        ensure_voice_exists(voice_id, DATA_DIR, voices_dict)

        # Find the downloaded model files
        voice_info = voices_dict.get(voice_id, {})
        onnx_path = voice_info.get("path")
        if not onnx_path or not os.path.isfile(onnx_path):
            # Try to find manually
            for f in os.listdir(DATA_DIR):
                if voice_id.lower().replace("-", "_") in f.lower() and f.endswith(".onnx"):
                    onnx_path = os.path.join(DATA_DIR, f)
                    break

        if not onnx_path or not os.path.isfile(onnx_path):
            return None, f"Voice model not found after download: {voice_id}"

        # Load voice
        voice = PiperVoice.load(onnx_path)
        LOADED_VOICES[voice_id] = voice
        return voice, None
    except Exception as e:
        return None, str(e)


HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TTS - AI Hub Madrid</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;padding:1rem}.container{max-width:800px;margin:0 auto;padding:1.5rem}.header{text-align:center;margin-bottom:2rem}.icon{font-size:3rem}.h1{font-size:2rem;font-weight:800;color:#fff;margin:.5rem 0}.badge{display:inline-block;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1rem}.ok{background:rgba(34,197,94,.15);color:#22c55e}.err{background:rgba(239,68,68,.15);color:#ef4444}.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:2rem;margin-bottom:1.5rem}label{display:block;font-size:.9rem;color:#9ca3af;margin-bottom:.5rem;font-weight:600}textarea,select{width:100%;background:#0f0f1a;border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:.8rem;color:#e0e0e0;font-size:1rem;font-family:inherit;margin-bottom:1rem}textarea{min-height:120px;resize:vertical}button{width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;border-radius:10px;padding:1rem;font-size:1.1rem;font-weight:700;cursor:pointer;transition:.2s}button:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(99,102,241,.3)}button:disabled{opacity:.5;cursor:not-allowed}audio{width:100%;margin-top:1rem}.footer{text-align:center;margin-top:2rem;color:#4b5563;font-size:.8rem}a{color:#6366f1}.row{display:flex;gap:1rem}.col{flex:1}</style></head><body><div class="container"><div class="header"><div class="icon">\U0001F3A4</div><h1 class="h1">Text to Speech</h1><div class="badge" id="badge">Checking...</div></div><div class="card"><label for="text">Texto a sintetizar</label><textarea id="text">Hola, este es un test del servicio de sintesis de voz del AI Hub Madrid.</textarea><div class="row"><div class="col"><label for="voice">Voz</label><select id="voice"><optgroup label="Espa\u00f1ol"><option value="es_ES-sharvard-medium">Sharvard</option><option value="es_ES-Beatriz-medium">Beatriz</option><option value="es_ES-Davefx-medium">Davefx</option></optgroup><optgroup label="English"><option value="en_US-amy-medium">Amy (US)</option><option value="en_GB-alan-medium">Alan (UK)</option></optgroup><optgroup label="Otros"><option value="fr_FR-siwis-medium">Siwis (FR)</option><option value="de_DE-thorsten-medium">Thorsten (DE)</option></optgroup></select></div><div class="col"><label for="speed">Velocidad</label><select id="speed"><option value="1.0">Normal</option><option value="0.8">Lenta</option><option value="1.2">Rapida</option></select></div></div><button id="btn" onclick="gen()">Generar Audio</button><audio id="p" controls style="display:none"></audio><div id="err" style="color:#ef4444;margin-top:1rem;display:none"></div></div><div class="footer">AI Hub Madrid \u00b7 <a href="http://100.105.27.27:3000">Hub</a></div></div><script>fetch('/api/status').then(r=>r.json()).then(s=>{const b=document.getElementById('badge');if(s.ready){b.className='badge ok';b.textContent='\u2705 Listo'}else{b.className='badge err';b.textContent='\u274C '+s.error}});async function gen(){const b=document.getElementById('btn');const t=document.getElementById('text').value.trim();if(!t)return alert('Escribe texto');const v=document.getElementById('voice').value;const s=document.getElementById('speed').value;b.disabled=true;b.textContent='Generando...';document.getElementById('err').style.display='none';try{const fd=new FormData();fd.append('text',t);fd.append('voice',v);fd.append('speed',s);const r=await fetch('/api/tts',{method:'POST',body:fd});if(!r.ok){const e=await r.json();throw new Error(e.detail||'Error')}const bl=await r.blob();const u=URL.createObjectURL(bl);const p=document.getElementById('p');p.src=u;p.style.display='block';p.play()}catch(e){const d=document.getElementById('err');d.textContent=e.message;d.style.display='block'}finally{b.disabled=false;b.textContent='Generar Audio'}}</script></body></html>"""


@app.get("/")
async def root():
    return HTMLResponse(HTML)


@app.get("/api/status")
async def status():
    return {
        "loading": False,
        "ready": PIPER_PY,
        "device": "CPU",
        "model": "piper-tts",
        "error": None if PIPER_PY else "piper-tts package not installed"
    }


@app.post("/api/tts")
async def tts(text: str = Form(...), voice: str = Form(DEFAULT_VOICE), speed: float = Form(1.0)):
    if not PIPER_PY:
        return JSONResponse({"detail": "piper-tts not installed"}, status_code=503)

    v, err = load_voice(voice)
    if err:
        return JSONResponse({"detail": f"Voice error: {err}"}, status_code=500)

    try:
        # Generate audio to buffer
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            v.synthesize(text, wav_file, length_scale=1.0/speed)

        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/wav",
                                 headers={"Content-Disposition": "attachment; filename=tts.wav"})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"detail": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
'''

def main():
    print("=" * 60)
    print("FIX FINAL: Piper TTS via Python package")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    print("Conectado!\n")

    # 1. Detener TTS
    print("[1] Deteniendo TTS...")
    run(ssh, "echo pepe1234 | sudo -S systemctl stop tts 2>&1")

    # 2. Instalar piper-tts Python package
    print("\n[2] Instalando piper-tts...")
    out = run(ssh, "/home/pepe/ai_env/bin/pip install piper-tts 2>&1", timeout=300)
    if "Successfully" in out or "already satisfied" in out:
        print("    piper-tts instalado OK")
    else:
        print(f"    Resultado: {out[-300:]}")

    # Verificar
    out = run(ssh, "/home/pepe/ai_env/bin/python -c 'from piper.voice import PiperVoice; print(\"OK\")' 2>&1")
    print(f"    Import test: {out.strip()}")

    # 3. Subir nuevo tts_svc.py
    print("\n[3] Subiendo nuevo tts_svc.py...")
    sftp = ssh.open_sftp()
    with sftp.file("/home/pepe/tts_svc.py", "w") as f:
        f.write(TTS_SERVICE)
    sftp.close()
    print("    Subido")

    # 4. Limpiar modelos viejos corruptos
    print("\n[4] Limpiando modelos viejos...")
    run(ssh, "rm -rf /mnt/seagate/models/tts/piper/models/* 2>/dev/null")
    run(ssh, "mkdir -p /mnt/seagate/models/tts/piper/models")

    # 5. Reiniciar
    print("\n[5] Reiniciando TTS...")
    run(ssh, "echo pepe1234 | sudo -S systemctl reset-failed tts 2>&1")
    run(ssh, "echo pepe1234 | sudo -S systemctl start tts 2>&1")
    time.sleep(5)

    status = run(ssh, "systemctl is-active tts").strip()
    print(f"    TTS: {status}")

    out = run(ssh, "curl -s http://localhost:8010/api/status 2>/dev/null")
    print(f"    Status: {out.strip()}")

    # 6. Test (primera vez descarga el modelo, puede tardar)
    print("\n[6] Test TTS (primera vez = descarga modelo, esperar 30-60s)...")
    test_cmd = "curl -s -X POST http://localhost:8010/api/tts -F 'text=Hola mundo' -F 'voice=es_ES-sharvard-medium' -o /tmp/test_final.wav -w '%{http_code}' --max-time 120 2>/dev/null"
    out = run(ssh, test_cmd, timeout=180)
    print(f"    HTTP: {out.strip()}")

    out = run(ssh, "ls -lh /tmp/test_final.wav 2>/dev/null; file /tmp/test_final.wav 2>/dev/null")
    print(f"    Audio: {out.strip()}")

    # Si falla, ver logs
    out2 = run(ssh, "echo pepe1234 | sudo -S journalctl -u tts --no-pager -n 25 2>&1")
    print(f"\n    Logs:\n{out2.strip()[-600:]}")

    # STT
    print("\n[7] STT status...")
    out = run(ssh, "systemctl is-active stt; curl -s http://localhost:8020/api/status 2>/dev/null")
    print(f"    {out.strip()}")

    # GPU
    out = run(ssh, "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null")
    print(f"\n    GPU: {out.strip()}")

    ssh.close()
    print("\n" + "=" * 60)
    print("DONE!")

if __name__ == "__main__":
    main()
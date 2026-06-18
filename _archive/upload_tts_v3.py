#!/usr/bin/env python3
"""Upload tts_svc.py with correct piper 1.4.2 synthesize API (returns AudioChunk iterable)."""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SERVICE_CODE = r'''#!/usr/bin/env python3
"""Piper TTS Service - AI Hub Madrid (piper-tts 1.4.2)"""
import os, sys, io, traceback, wave
from pathlib import Path

os.environ["HOME"] = "/home/pepe"
os.environ["XDG_CACHE_HOME"] = "/mnt/seagate/cache"

from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import uvicorn

from piper import PiperVoice, SynthesisConfig
from piper.download_voices import download_voice

app = FastAPI(title="Piper TTS - AI Hub Madrid")

DATA_DIR = Path("/mnt/seagate/models/tts/piper/models")
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_VOICE = "es_ES-sharvard-medium"
LOADED_VOICES = {}

def find_onnx(voice_id):
    expected = DATA_DIR / f"{voice_id}.onnx"
    if expected.is_file():
        return str(expected)
    voice_lower = voice_id.lower().replace("-", "_")
    for root, dirs, files in os.walk(str(DATA_DIR)):
        for f in files:
            if f.endswith(".onnx") and voice_lower in f.lower():
                return os.path.join(root, f)
    return None

def load_voice(voice_id):
    if voice_id in LOADED_VOICES:
        return LOADED_VOICES[voice_id], None
    try:
        onnx_path = find_onnx(voice_id)
        if not onnx_path:
            print(f"Downloading voice: {voice_id}")
            download_voice(voice_id, DATA_DIR)
            onnx_path = find_onnx(voice_id)
        if not onnx_path:
            return None, f"Voice model not found: {voice_id}"
        print(f"Loading voice: {onnx_path}")
        voice = PiperVoice.load(onnx_path)
        LOADED_VOICES[voice_id] = voice
        return voice, None
    except Exception as e:
        traceback.print_exc()
        return None, str(e)

HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TTS - AI Hub Madrid</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;padding:1rem}.container{max-width:800px;margin:0 auto;padding:1.5rem}.header{text-align:center;margin-bottom:2rem}.icon{font-size:3rem}.h1{font-size:2rem;font-weight:800;color:#fff;margin:.5rem 0}.badge{display:inline-block;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1rem}.ok{background:rgba(34,197,94,.15);color:#22c55e}.err{background:rgba(239,68,68,.15);color:#ef4444}.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:2rem;margin-bottom:1.5rem}label{display:block;font-size:.9rem;color:#9ca3af;margin-bottom:.5rem;font-weight:600}textarea,select{width:100%;background:#0f0f1a;border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:.8rem;color:#e0e0e0;font-size:1rem;font-family:inherit;margin-bottom:1rem}textarea{min-height:120px;resize:vertical}button{width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;border-radius:10px;padding:1rem;font-size:1.1rem;font-weight:700;cursor:pointer;transition:.2s}button:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(99,102,241,.3)}button:disabled{opacity:.5;cursor:not-allowed}audio{width:100%;margin-top:1rem}.footer{text-align:center;margin-top:2rem;color:#4b5563;font-size:.8rem}a{color:#6366f1}.row{display:flex;gap:1rem}.col{flex:1}</style></head><body><div class="container"><div class="header"><div class="icon">\U0001F3A4</div><h1 class="h1">Text to Speech</h1><div class="badge" id="badge">Checking...</div></div><div class="card"><label for="text">Texto a sintetizar</label><textarea id="text">Hola, este es un test del servicio de s\u00edntesis de voz del AI Hub Madrid.</textarea><div class="row"><div class="col"><label for="voice">Voz</label><select id="voice"><optgroup label="Espa\u00f1ol"><option value="es_ES-sharvard-medium">Sharvard</option><option value="es_ES-Beatriz-medium">Beatriz</option><option value="es_ES-Davefx-medium">Davefx</option></optgroup><optgroup label="English"><option value="en_US-amy-medium">Amy (US)</option><option value="en_GB-alan-medium">Alan (UK)</option></optgroup><optgroup label="Otros"><option value="fr_FR-siwis-medium">Siwis (FR)</option><option value="de_DE-thorsten-medium">Thorsten (DE)</option></optgroup></select></div><div class="col"><label for="speed">Velocidad</label><select id="speed"><option value="1.0">Normal</option><option value="0.8">Lenta</option><option value="1.2">Rapida</option></select></div></div><button id="btn" onclick="gen()">Generar Audio</button><audio id="p" controls style="display:none"></audio><div id="err" style="color:#ef4444;margin-top:1rem;display:none"></div></div><div class="footer">AI Hub Madrid \u00b7 <a href="http://100.105.27.27:3000">Hub</a></div></div><script>fetch('/api/status').then(r=>r.json()).then(s=>{const b=document.getElementById('badge');if(s.ready){b.className='badge ok';b.textContent='\u2705 Listo'}else{b.className='badge err';b.textContent='\u274C '+s.error}});async function gen(){const b=document.getElementById('btn');const t=document.getElementById('text').value.trim();if(!t)return alert('Escribe texto');const v=document.getElementById('voice').value;const s=document.getElementById('speed').value;b.disabled=true;b.textContent='Generando...';document.getElementById('err').style.display='none';try{const fd=new FormData();fd.append('text',t);fd.append('voice',v);fd.append('speed',s);const r=await fetch('/api/tts',{method:'POST',body:fd});if(!r.ok){const e=await r.json();throw new Error(e.detail||'Error')}const bl=await r.blob();const u=URL.createObjectURL(bl);const p=document.getElementById('p');p.src=u;p.style.display='block';p.play()}catch(e){const d=document.getElementById('err');d.textContent=e.message;d.style.display='block'}finally{b.disabled=false;b.textContent='Generar Audio'}}</script></body></html>"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

@app.get("/api/status")
async def status():
    return {"loading": False, "ready": True, "device": "CPU", "model": "piper-tts", "error": None}

@app.post("/api/tts")
async def tts(text: str = Form(...), voice: str = Form(DEFAULT_VOICE), speed: float = Form(1.0)):
    v, err = load_voice(voice)
    if err:
        return JSONResponse({"detail": str(err)}, status_code=500)
    try:
        # piper 1.4.2: synthesize() returns Iterable[AudioChunk]
        # AudioChunk has: sample_rate, sample_width, sample_channels, audio_int16_bytes
        syn_config = SynthesisConfig(length_scale=1.0/speed)

        # Collect all chunks
        chunks = list(v.synthesize(text, syn_config))
        if not chunks:
            return JSONResponse({"detail": "No audio generated"}, status_code=500)

        # Get audio params from first chunk
        sample_rate = chunks[0].sample_rate
        sample_width = chunks[0].sample_width
        sample_channels = chunks[0].sample_channels

        # Write WAV to buffer
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setframerate(sample_rate)
            wav_file.setsampwidth(sample_width)
            wav_file.setnchannels(sample_channels)
            for chunk in chunks:
                wav_file.writeframes(chunk.audio_int16_bytes)

        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/wav",
                                 headers={"Content-Disposition": "attachment; filename=tts.wav"})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"detail": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)
print("Conectado!")

# Upload
sftp = ssh.open_sftp()
with sftp.file('/home/pepe/tts_svc.py', 'w') as f:
    f.write(SERVICE_CODE)
sftp.close()
print("tts_svc.py subido (synthesize -> AudioChunk)")

# Restart
stdin, stdout, stderr = ssh.exec_command('echo pepe1234 | sudo -S systemctl restart tts 2>&1')
stdout.channel.recv_exit_status()
time.sleep(6)

# Status
_, o, _ = ssh.exec_command('systemctl is-active tts')
print(f"TTS: {o.read().decode().strip()}")

_, o, _ = ssh.exec_command('curl -s http://localhost:8010/api/status 2>/dev/null')
print(f"Status: {o.read().decode().strip()}")

# Test
print("\nTest TTS...")
_, o, _ = ssh.exec_command(
    "curl -s -X POST http://localhost:8010/api/tts -F 'text=Hola mundo, esta es una prueba' -F 'voice=es_ES-sharvard-medium' -o /tmp/tts_final.wav -w '%{http_code}' --max-time 60 2>/dev/null",
    timeout=90)
print(f"HTTP: {o.read().decode().strip()}")

_, o, _ = ssh.exec_command('ls -lh /tmp/tts_final.wav 2>/dev/null; file /tmp/tts_final.wav 2>/dev/null')
print(f"Audio: {o.read().decode('utf-8','replace').strip()}")

# Logs
_, o, _ = ssh.exec_command('echo pepe1234 | sudo -S journalctl -u tts --no-pager -n 10 2>&1')
print(f"\nLogs: {o.read().decode('utf-8','replace').strip()[-500:]}")

ssh.close()
print("\nDone!")
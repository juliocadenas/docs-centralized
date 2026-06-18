#!/usr/bin/env python3
"""Upload fixed tts_svc.py and test."""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SERVICE_CODE = '''#!/usr/bin/env python3
"""Piper TTS Service - AI Hub Madrid"""
import os, sys, io, traceback, wave

os.environ["HOME"] = "/home/pepe"
os.environ["XDG_CACHE_HOME"] = "/mnt/seagate/cache"

from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import uvicorn

from piper import PiperVoice
from piper.download_voices import get_voices, ensure_voice_exists

app = FastAPI(title="Piper TTS - AI Hub Madrid")

DATA_DIR = "/mnt/seagate/models/tts/piper/models"
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_VOICE = "es_ES-sharvard-medium"
LOADED_VOICES = {}

def load_voice(voice_id):
    if voice_id in LOADED_VOICES:
        return LOADED_VOICES[voice_id], None
    try:
        voices_dict = get_voices(DATA_DIR)
        ensure_voice_exists(voice_id, DATA_DIR, voices_dict)
        voice_info = voices_dict.get(voice_id, {})
        onnx_path = voice_info.get("path")
        if not onnx_path or not os.path.isfile(onnx_path):
            for root, dirs, files in os.walk(DATA_DIR):
                for f in files:
                    if f.endswith(".onnx") and voice_id.lower() in f.lower():
                        onnx_path = os.path.join(root, f)
                        break
        if not onnx_path or not os.path.isfile(onnx_path):
            return None, f"Voice model not found: {voice_id}"
        voice = PiperVoice.load(onnx_path)
        LOADED_VOICES[voice_id] = voice
        return voice, None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>TTS - AI Hub</title></head><body style="background:#0f0f1a;color:#fff;font-family:sans-serif;padding:2rem"><h1>TTS Service</h1><p>POST /api/tts with text, voice, speed</p></body></html>"""

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

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)
print("Conectado!")

# Upload
sftp = ssh.open_sftp()
with sftp.file('/home/pepe/tts_svc.py', 'w') as f:
    f.write(SERVICE_CODE)
sftp.close()
print("tts_svc.py subido")

# Restart
stdin, stdout, stderr = ssh.exec_command('echo pepe1234 | sudo -S systemctl restart tts 2>&1')
stdout.channel.recv_exit_status()
time.sleep(6)

# Status
_, o, _ = ssh.exec_command('systemctl is-active tts')
print(f"TTS: {o.read().decode().strip()}")

_, o, _ = ssh.exec_command('curl -s http://localhost:8010/api/status 2>/dev/null')
print(f"Status: {o.read().decode().strip()}")

# Logs
_, o, _ = ssh.exec_command('echo pepe1234 | sudo -S journalctl -u tts --no-pager -n 15 2>&1')
print(f"Logs: {o.read().decode('utf-8','replace').strip()[-500:]}")

ssh.close()
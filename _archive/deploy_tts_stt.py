#!/usr/bin/env python3
"""
Deploy completo TTS + STT al NAB9.
- TTS: XTTS-v2 (Coqui TTS) en puerto 8010
- STT: Whisper large-v3 en puerto 8020
Crea servicios systemd persistentes.
"""
import paramiko
import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

# ============================================================
# TTS SERVICE - XTTS-v2 (puerto 8010)
# ============================================================
TTS_SERVICE = r'''#!/usr/bin/env python3
"""XTTS-v2 Text-to-Speech Service - AI Hub Madrid"""
import os, sys, io, traceback, time

# Ensure model cache goes to seagate
os.environ["HOME"] = "/home/pepe"
os.environ["TORCH_HOME"] = "/mnt/seagate/models/tts"
os.environ["XDG_CACHE_HOME"] = "/mnt/seagate/cache"
os.environ["COQUI_TOS_AGREED"] = "1"

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import uvicorn, torch

app = FastAPI(title="XTTS-v2 TTS - AI Hub Madrid")

MODEL = None
LOADING = True
LOAD_ERROR = None

def load_model():
    global MODEL, LOADING, LOAD_ERROR
    try:
        from TTS.api import TTS
        device = "cuda" if torch.cuda.is_available() else "cpu"
        MODEL = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=(device=="cuda"))
        print(f"XTTS-v2 loaded on {device}")
    except Exception as e:
        LOAD_ERROR = str(e)
        traceback.print_exc()
    finally:
        LOADING = False

import threading
threading.Thread(target=load_model, daemon=True).start()

HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>XTTS-v2 - AI Hub Madrid</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;padding:1rem}.container{max-width:800px;margin:0 auto;padding:1.5rem}.header{text-align:center;margin-bottom:2rem}.icon{font-size:3rem}.h1{font-size:2rem;font-weight:800;color:#fff;margin:.5rem 0}.badge{display:inline-block;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1rem}.badge.ready{background:rgba(34,197,94,.15);color:#22c55e}.badge.loading{background:rgba(245,158,11,.15);color:#f59e0b}.badge.error{background:rgba(239,68,68,.15);color:#ef4444}.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:2rem;margin-bottom:1.5rem}label{display:block;font-size:.9rem;color:#9ca3af;margin-bottom:.5rem;font-weight:600}textarea,input,select{width:100%;background:#0f0f1a;border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:.8rem;color:#e0e0e0;font-size:1rem;font-family:inherit;margin-bottom:1rem}textarea{min-height:100px;resize:vertical}button{width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;border-radius:10px;padding:1rem;font-size:1.1rem;font-weight:700;cursor:pointer;transition:.2s}button:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(99,102,241,.3)}button:disabled{opacity:.5;cursor:not-allowed}audio{width:100%;margin-top:1rem}info{color:#6b7280;font-size:.8rem}.footer{text-align:center;margin-top:2rem;color:#4b5563;font-size:.8rem}a{color:#6366f1}.row{display:flex;gap:1rem}.col{flex:1}.ref-audio{border:2px dashed rgba(255,255,255,.1);border-radius:10px;padding:1rem;text-align:center;cursor:pointer;transition:.2s}.ref-audio:hover{border-color:#6366f1}.ref-audio.has-file{border-color:#22c55e;background:rgba(34,197,94,.05)}</style></head><body><div class="container"><div class="header"><div class="icon">🎙️</div><h1 class="h1">XTTS-v2</h1><div id="status" class="badge loading">⏳ Cargando modelo...</div></div><div class="card"><div class="row"><div class="col"><label for="text">Texto a sintetizar</label><textarea id="text" placeholder="Escribe aqui el texto que quieres convertir a voz...">Hola, este es un test de sintesis de voz con XTTS-v2 en el AI Hub Madrid.</textarea></div></div><div class="row"><div class="col"><label for="lang">Idioma</label><select id="lang"><option value="es">Español</option><option value="en">English</option><option value="fr">Français</option><option value="de">Deutsch</option><option value="it">Italiano</option><option value="pt">Português</option><option value="nl">Nederlands</option><option value="pl">Polski</option><option value="tr">Türkçe</option><option value="ru">Русский</option><option value="ja">日本語</option><option value="zh">中文</option><option value="ko">한국어</option><option value="ar">العربية</option><option value="cs">Čeština</option><option value="hu">Magyar</option><option value="hi">हिन्दी</option></select></div><div class="col"><label>Voz de referencia (opcional)</label><div class="ref-audio" id="dropZone"><input type="file" id="refAudio" accept="audio/*" style="display:none"><p id="refLabel">🔊 Click para subir voz de referencia<br><small>Clona cualquier voz con 3+ segundos de audio</small></p></div></div></div><button id="btn" onclick="generate()" disabled>🎵 Generar Audio</button><audio id="player" controls style="display:none"></audio><div id="error" style="color:#ef4444;margin-top:1rem;display:none"></div></div><div class="footer">AI Hub Madrid &middot; XTTS-v2 (Coqui TTS) &middot; <a href="http://100.105.27.27:3000">Volver al Hub</a></div></div><script>const drop=document.getElementById('dropZone');const fileInput=document.getElementById('refAudio');const refLabel=document.getElementById('refLabel');drop.onclick=()=>fileInput.click();fileInput.onchange=e=>{if(e.target.files.length){refLabel.textContent='✅ '+e.target.files[0].name;drop.classList.add('has-file')}};async function checkStatus(){try{const r=await fetch('/api/status');const d=await r.json();const s=document.getElementById('status');const b=document.getElementById('btn');if(d.loading){s.className='badge loading';s.textContent='⏳ Cargando modelo...';b.disabled=true}else if(d.error){s.className='badge error';s.textContent='❌ Error: '+d.error.substring(0,80);b.disabled=true}else if(d.ready){s.className='badge ready';s.textContent='✅ Listo - GPU: '+d.device;b.disabled=false}else{setTimeout(checkStatus,3000)}}catch(e){setTimeout(checkStatus,3000)}}checkStatus();async function generate(){const btn=document.getElementById('btn');const text=document.getElementById('text').value;const lang=document.getElementById('lang').value;const file=fileInput.files[0];btn.disabled=true;btn.textContent='⏳ Generando...';document.getElementById('error').style.display='none';try{const fd=new FormData();fd.append('text',text);fd.append('language',lang);if(file)fd.append('ref_audio',file);const r=await fetch('/api/tts',{method:'POST',body:fd});if(!r.ok){const e=await r.json();throw new Error(e.detail||'Error generando audio')}const blob=await r.blob();const url=URL.createObjectURL(blob);const player=document.getElementById('player');player.src=url;player.style.display='block';player.play()}catch(e){const errDiv=document.getElementById('error');errDiv.textContent='❌ '+e.message;errDiv.style.display='block'}finally{btn.disabled=false;btn.textContent='🎵 Generar Audio'}}</script></body></html>"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

@app.get("/api/status")
async def status():
    if LOADING:
        return {"loading": True, "ready": False}
    if LOAD_ERROR:
        return {"loading": False, "ready": False, "error": LOAD_ERROR}
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return {"loading": False, "ready": True, "device": device, "model": "xtts_v2"}

@app.post("/api/tts")
async def tts(text: str = Form(...), language: str = Form("es"), ref_audio: UploadFile = File(None)):
    if MODEL is None:
        return JSONResponse({"detail": "Model not loaded"}, status_code=503)

    # Save ref audio if provided
    ref_path = None
    if ref_audio:
        ref_path = "/tmp/tts_ref.wav"
        with open(ref_path, "wb") as f:
            f.write(await ref_audio.read())

    # Generate
    out_path = "/tmp/tts_output.wav"
    try:
        if ref_path:
            MODEL.tts_to_file(
                text=text,
                language=language,
                speaker_wav=ref_path,
                file_path=out_path,
                split_sentences=True
            )
        else:
            # Default speaker
            MODEL.tts_to_file(
                text=text,
                language=language,
                speaker="Ana Florence",
                file_path=out_path,
                split_sentences=True
            )

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

# ============================================================
# STT SERVICE - Whisper large-v3 (puerto 8020)
# ============================================================
STT_SERVICE = r'''#!/usr/bin/env python3
"""Whisper large-v3 Speech-to-Text Service - AI Hub Madrid"""
import os, sys, io, traceback, tempfile, time

# Ensure model cache goes to seagate
os.environ["HOME"] = "/home/pepe"
os.environ["TORCH_HOME"] = "/mnt/seagate/models/stt"
os.environ["XDG_CACHE_HOME"] = "/mnt/seagate/cache"

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn, torch

app = FastAPI(title="Whisper STT - AI Hub Madrid")

MODEL = None
LOADING = True
LOAD_ERROR = None

def load_model():
    global MODEL, LOADING, LOAD_ERROR
    try:
        import whisper
        device = "cuda" if torch.cuda.is_available() else "cpu"
        MODEL = whisper.load_model("large-v3", device=device, download_root="/mnt/seagate/models/stt")
        print(f"Whisper large-v3 loaded on {device}")
    except Exception as e:
        LOAD_ERROR = str(e)
        traceback.print_exc()
    finally:
        LOADING = False

import threading
threading.Thread(target=load_model, daemon=True).start()

HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Whisper v3 - AI Hub Madrid</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;padding:1rem}.container{max-width:800px;margin:0 auto;padding:1.5rem}.header{text-align:center;margin-bottom:2rem}.icon{font-size:3rem}.h1{font-size:2rem;font-weight:800;color:#fff;margin:.5rem 0}.badge{display:inline-block;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1rem}.badge.ready{background:rgba(34,197,94,.15);color:#22c55e}.badge.loading{background:rgba(245,158,11,.15);color:#f59e0b}.badge.error{background:rgba(239,68,68,.15);color:#ef4444}.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:2rem;margin-bottom:1.5rem}.upload-zone{border:2px dashed rgba(255,255,255,.15);border-radius:14px;padding:3rem;text-align:center;cursor:pointer;transition:.2s;margin-bottom:1rem}.upload-zone:hover{border-color:#6366f1;background:rgba(99,102,241,.05)}.upload-zone.has-file{border-color:#22c55e;background:rgba(34,197,94,.05)}.upload-icon{font-size:3rem;margin-bottom:1rem}.upload-text{color:#9ca3af}button{width:100%;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;border-radius:10px;padding:1rem;font-size:1.1rem;font-weight:700;cursor:pointer;transition:.2s;margin-bottom:1rem}button:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(99,102,241,.3)}button:disabled{opacity:.5;cursor:not-allowed}.result{background:#0f0f1a;border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:1.5rem;margin-top:1rem;white-space:pre-wrap;word-wrap:break-word;min-height:100px;font-size:1rem;line-height:1.6}.result:empty:before{content:'La transcripcion aparecera aqui...';color:#4b5563}.options{display:flex;gap:1rem;margin-bottom:1rem}.option{flex:1}select{width:100%;background:#0f0f1a;border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:.6rem;color:#e0e0e0}label{display:block;font-size:.85rem;color:#9ca3af;margin-bottom:.3rem}info{color:#6b7280;font-size:.8rem}.footer{text-align:center;margin-top:2rem;color:#4b5563;font-size:.8rem}a{color:#6366f1}.record-btn{background:rgba(239,68,68,.2)!important;border:1px solid rgba(239,68,68,.3)!important}.record-btn:hover{background:rgba(239,68,68,.3)!important}</style></head><body><div class="container"><div class="header"><div class="icon">🎤</div><h1 class="h1">Whisper large-v3</h1><div id="status" class="badge loading">⏳ Cargando modelo...</div></div><div class="card"><div class="options"><div class="option"><label>Idioma</label><select id="lang"><option value="">Auto-detectar</option><option value="es">Español</option><option value="en">English</option><option value="fr">Français</option><option value="de">Deutsch</option><option value="it">Italiano</option><option value="pt">Português</option><option value="ru">Русский</option><option value="ja">日本語</option><option value="zh">中文</option></select></div><div class="option"><label>Tarea</label><select id="task"><option value="transcribe">Transcribir</option><option value="translate">Traducir al inglés</option></select></div></div><div class="upload-zone" id="dropZone"><input type="file" id="audioFile" accept="audio/*,video/*" style="display:none"><div class="upload-icon">📁</div><div class="upload-text" id="dropLabel">Click o arrastra audio aqui<br><small>MP3, WAV, M4A, FLAC, OGG, MP4...</small></div></div><button id="btn" onclick="transcribe()" disabled>📝 Transcribir</button><button id="recBtn" class="record-btn" onclick="toggleRecord()">🔴 Grabar desde el micrófono</button><div id="result" class="result"></div><div id="error" style="color:#ef4444;margin-top:1rem;display:none"></div></div><div class="footer">AI Hub Madrid &middot; Whisper large-v3 (OpenAI) &middot; <a href="http://100.105.27.27:3000">Volver al Hub</a></div></div><script>let mediaRecorder=null;let audioChunks=[];const drop=document.getElementById('dropZone');const fileInput=document.getElementById('audioFile');const dropLabel=document.getElementById('dropLabel');drop.onclick=()=>fileInput.click();fileInput.onchange=e=>{if(e.target.files.length){dropLabel.textContent='✅ '+e.target.files[0].name;drop.classList.add('has-file')}};drop.ondragover=e=>{e.preventDefault();drop.style.borderColor='#6366f1'};drop.ondragleave=()=>{drop.style.borderColor=''};drop.ondrop=e=>{e.preventDefault();if(e.dataTransfer.files.length){fileInput.files=e.dataTransfer.files;dropLabel.textContent='✅ '+e.dataTransfer.files[0].name;drop.classList.add('has-file');drop.style.borderColor=''}};async function checkStatus(){try{const r=await fetch('/api/status');const d=await r.json();const s=document.getElementById('status');const b=document.getElementById('btn');if(d.loading){s.className='badge loading';s.textContent='⏳ Cargando modelo...';b.disabled=true}else if(d.error){s.className='badge error';s.textContent='❌ '+d.error.substring(0,80);b.disabled=true}else if(d.ready){s.className='badge ready';s.textContent='✅ Listo - GPU: '+d.device;b.disabled=false}else{setTimeout(checkStatus,5000)}}catch(e){setTimeout(checkStatus,5000)}}checkStatus();async function transcribe(file){const btn=document.getElementById('btn');const result=document.getElementById('result');const errDiv=document.getElementById('error');const file2=file||fileInput.files[0];if(!file2){errDiv.textContent='Sube un archivo de audio primero';errDiv.style.display='block';return}btn.disabled=true;btn.textContent='⏳ Transcribiendo...';errDiv.style.display='none';result.textContent='';try{const fd=new FormData();fd.append('audio',file2);fd.append('language',document.getElementById('lang').value);fd.append('task',document.getElementById('task').value);const r=await fetch('/api/transcribe',{method:'POST',body:fd});if(!r.ok){const e=await r.json();throw new Error(e.detail||'Error')}const d=await r.json();result.textContent=d.text}catch(e){errDiv.textContent='❌ '+e.message;errDiv.style.display='block'}finally{btn.disabled=false;btn.textContent='📝 Transcribir'}}async function toggleRecord(){const btn=document.getElementById('recBtn');if(mediaRecorder&&mediaRecorder.state==='recording'){mediaRecorder.stop();return}try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});mediaRecorder=new MediaRecorder(stream);audioChunks=[];mediaRecorder.ondataavailable=e=>audioChunks.push(e.data);mediaRecorder.onstop=async()=>{btn.textContent='🔴 Grabar desde el micrófono';btn.classList.add('record-btn');const blob=new Blob(audioChunks,{type:'audio/webm'});const file=new File([blob],'recording.webm',{type:'audio/webm'});dropLabel.textContent='✅ recording.webm';drop.classList.add('has-file');stream.getTracks().forEach(t=>t.stop());await transcribe(file)};mediaRecorder.start();btn.textContent='⏹️ Detener grabación';btn.classList.remove('record-btn')}catch(e){alert('No se pudo acceder al micrófono: '+e.message)}}document.getElementById('btn').onclick=()=>transcribe()</script></body></html>"""

@app.get("/")
async def root():
    return HTMLResponse(HTML)

@app.get("/api/status")
async def status():
    if LOADING:
        return {"loading": True, "ready": False}
    if LOAD_ERROR:
        return {"loading": False, "ready": False, "error": LOAD_ERROR}
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return {"loading": False, "ready": True, "device": device, "model": "whisper-large-v3"}

@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = Form(""), task: str = Form("transcribe")):
    if MODEL is None:
        return JSONResponse({"detail": "Model not loaded"}, status_code=503)

    # Save uploaded audio to temp file
    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        options = {}
        if language:
            options["language"] = language
        options["task"] = task

        result = MODEL.transcribe(tmp_path, **options)
        return {"text": result["text"], "language": result.get("language", "unknown")}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"detail": str(e)}, status_code=500)
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8020)
'''

# ============================================================
# SYSTEMD SERVICE FILES
# ============================================================
TTS_SYSTEMD = """[Unit]
Description=XTTS-v2 TTS Service
After=network.target docker.service
Wants=network.target

[Service]
Type=simple
User=pepe
ExecStart=/home/pepe/ai_env/bin/python /home/pepe/tts_svc.py
Restart=on-failure
RestartSec=10
Environment=HOME=/home/pepe
Environment=COQUI_TOS_AGREED=1
Environment=TORCH_HOME=/mnt/seagate/models/tts
Environment=XDG_CACHE_HOME=/mnt/seagate/cache
WorkingDirectory=/home/pepe

[Install]
WantedBy=multi-user.target
"""

STT_SYSTEMD = """[Unit]
Description=Whisper large-v3 STT Service
After=network.target docker.service
Wants=network.target

[Service]
Type=simple
User=pepe
ExecStart=/home/pepe/ai_env/bin/python /home/pepe/stt_svc.py
Restart=on-failure
RestartSec=10
Environment=HOME=/home/pepe
Environment=TORCH_HOME=/mnt/seagate/models/stt
Environment=XDG_CACHE_HOME=/mnt/seagate/cache
WorkingDirectory=/home/pepe

[Install]
WantedBy=multi-user.target
"""

def run_cmd(ssh, cmd, timeout=300):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

def main():
    print("=" * 60)
    print("DEPLOY TTS + STT al NAB9")
    print("=" * 60)

    # Conectar
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=20)
    print("Conectado!\n")

    # ===== 1. VERIFICAR QUE EXISTE EL VENV =====
    print("[1/6] Verificando entorno Python...")
    out, _ = run_cmd(ssh, "ls -la /home/pepe/ai_env/bin/python 2>/dev/null")
    if "ai_env" in out:
        print("   ai_env existe")
    else:
        print("   ai_env NO existe - creando...")
        run_cmd(ssh, "echo pepe1234 | sudo -S python3 -m venv /home/pepe/ai_env 2>&1", timeout=60)
        print("   ai_env creado")

    # ===== 2. INSTALAR DEPENDENCIAS =====
    print("\n[2/6] Instalando dependencias Python...")
    print("   Esto puede tardar varios minutos (TTS + whisper + torch)...")
    print("   Instalando en background - verificando cada 30s...")

    # Instalar todo en un solo comando
    install_cmd = (
        "echo pepe1234 | sudo -S /home/pepe/ai_env/bin/pip install "
        "TTS openai-whisper fastapi uvicorn python-multipart 2>&1"
    )
    # Ejecutar en background y monitorear
    transport = ssh.get_transport()
    channel = transport.open_session()
    channel.exec_command(install_cmd)

    dots = 0
    while True:
        if channel.exit_status_ready():
            break
        time.sleep(15)
        dots += 1
        print(f"   ...instalando ({dots*15}s)")

    out = channel.makefile('r', -1).read().decode('utf-8', errors='replace')
    err = channel.makefile_stderr('r', -1).read().decode('utf-8', errors='replace')

    # Check success
    if "Successfully installed" in out or "already satisfied" in out:
        print("   Dependencias instaladas!")
    else:
        print(f"   Output: {out[-500:]}")
        if err.strip():
            print(f"   Warnings: {err[-300:]}")

    # ===== 3. CREAR DIRECTORIOS DE CACHE EN SEAGATE =====
    print("\n[3/6] Creando directorios de cache...")
    run_cmd(ssh, "mkdir -p /mnt/seagate/models/tts /mnt/seagate/models/stt /mnt/seagate/cache")
    print("   Directorios creados")

    # ===== 4. SUBIR SCRIPTS =====
    print("\n[4/6] Subiendo servicios...")
    sftp = ssh.open_sftp()

    with sftp.file("/home/pepe/tts_svc.py", "w") as f:
        f.write(TTS_SERVICE)
    print("   tts_svc.py subido")

    with sftp.file("/home/pepe/stt_svc.py", "w") as f:
        f.write(STT_SERVICE)
    print("   stt_svc.py subido")

    # ===== 5. INSTALAR SYSTEMD SERVICES =====
    print("\n[5/6] Instalando systemd services...")

    # Upload service files to /tmp first
    with sftp.file("/tmp/tts.service", "w") as f:
        f.write(TTS_SYSTEMD)
    with sftp.file("/tmp/stt.service", "w") as f:
        f.write(STT_SYSTEMD)
    sftp.close()

    run_cmd(ssh, "echo pepe1234 | sudo -S cp /tmp/tts.service /etc/systemd/system/tts.service 2>&1")
    run_cmd(ssh, "echo pepe1234 | sudo -S cp /tmp/stt.service /etc/systemd/system/stt.service 2>&1")
    run_cmd(ssh, "echo pepe1234 | sudo -S systemctl daemon-reload 2>&1")
    run_cmd(ssh, "echo pepe1234 | sudo -S systemctl enable tts stt 2>&1")
    print("   Services instalados y habilitados")

    # ===== 6. INICIAR SERVICIOS =====
    print("\n[6/6] Iniciando servicios...")
    run_cmd(ssh, "echo pepe1234 | sudo -S systemctl start tts 2>&1")
    time.sleep(3)
    run_cmd(ssh, "echo pepe1234 | sudo -S systemctl start stt 2>&1")
    time.sleep(5)

    # Verificar
    out, _ = run_cmd(ssh, "systemctl is-active tts stt")
    print(f"   TTS: {run_cmd(ssh, 'systemctl is-active tts')[0].strip()}")
    print(f"   STT: {run_cmd(ssh, 'systemctl is-active stt')[0].strip()}")

    # Test HTTP
    time.sleep(5)
    for port, name in [(8010, "TTS"), (8020, "STT")]:
        out, _ = run_cmd(ssh, f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port} 2>/dev/null")
        print(f"   {name} :{port} -> HTTP {out.strip()}")

    # GPU check
    out, _ = run_cmd(ssh, "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null")
    print(f"\n   GPU VRAM: {out.strip()}")

    ssh.close()

    print("\n" + "=" * 60)
    print("DEPLOY COMPLETADO!")
    print("=" * 60)
    print("\nLos modelos se descargarán automáticamente al primer request:")
    print("  TTS: http://100.105.27.27:8010")
    print("  STT: http://100.105.27.27:8020")
    print("\nLos modelos (~6GB total) se guardan en /mnt/seagate/models/")
    print("Paciencia en el primer uso - tarda 2-3 min en cargar.")

if __name__ == "__main__":
    main()
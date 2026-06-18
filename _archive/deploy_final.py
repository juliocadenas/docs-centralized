#!/usr/bin/env python3
"""Patch gateway with TTS/STT endpoints and redeploy studio."""
import paramiko, sys, time, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd, timeout=120):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    return o.read().decode('utf-8','replace').strip(), e.read().decode('utf-8','replace').strip()

# Step 1: Check if TTS already exists
out, _ = run('grep -c "audio/speech" /home/pepe/ai-hub-gateway/gateway.py 2>/dev/null')
print(f"TTS endpoints already in gateway: {out}")

# Step 2: Backup
run('cp /home/pepe/ai-hub-gateway/gateway.py /home/pepe/ai-hub-gateway/gateway.py.bak2')
print("Gateway backed up")

# Step 3: Write patch script to server
patch_script = r'''
with open("/home/pepe/ai-hub-gateway/gateway.py", "r") as f:
    content = f.read()

if "/v1/audio/speech" not in content:
    patch = """

# === TTS/STT ENDPOINTS (Added by Cline) ===
from fastapi import UploadFile, File, Form as FastForm
from fastapi.responses import Response as FastResponse

@app.post("/v1/audio/speech")
async def tts_speech(request: dict):
    \"\"\"Text-to-Speech via Piper TTS (:8010). OpenAI-compatible.\"\"\"
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("http://localhost:8010/tts", json={
                "text": request.get("input", ""),
                "voice": request.get("voice", "es_ES-davefx-medium"),
                "language": request.get("language", "es"),
            })
            if resp.status_code != 200:
                return {"error": f"Piper TTS error: {resp.text}"}
            return FastResponse(content=resp.content, media_type="audio/wav")
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/audio/transcriptions")
async def stt_transcribe(
    file: UploadFile = File(...),
    language: str = FastForm("es"),
):
    \"\"\"Speech-to-Text via Whisper STT (:8020). OpenAI-compatible.\"\"\"
    import httpx
    try:
        audio_bytes = await file.read()
        files = {"file": (file.filename or "audio.wav", audio_bytes, file.content_type or "audio/wav")}
        data = {"language": language}
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post("http://localhost:8020/transcribe", files=files, data=data)
            if resp.status_code != 200:
                return {"error": f"Whisper STT error: {resp.text}"}
            return resp.json()
    except Exception as e:
        return {"error": str(e)}
"""
    if "if __name__" in content:
        content = content.replace("if __name__", patch + "\n\nif __name__")
    else:
        content = content + "\n\n" + patch

    with open("/home/pepe/ai-hub-gateway/gateway.py", "w") as f:
        f.write(content)
    print("PATCHED OK")
else:
    print("ALREADY HAS TTS")
'''

# Write the script to server via SFTP
sftp = ssh.open_sftp()
with sftp.file('/tmp/patch_gateway.py', 'w') as f:
    f.write(patch_script)
sftp.close()
print("Patch script uploaded")

# Step 4: Run patch
out, err = run('/home/pepe/comfyui_env/bin/python3 /tmp/patch_gateway.py 2>&1')
print(f"Patch result: {out}")
if err:
    print(f"Patch errors: {err}")

# Step 5: Restart gateway
print("Restarting gateway...")
run('echo pepe1234 | sudo -S systemctl restart ai-hub-gateway 2>/dev/null')
time.sleep(3)

# Step 6: Verify
out, _ = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/ 2>/dev/null')
print(f"Gateway :9000 status: {out}")

out, _ = run('curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/v1/audio/speech -H "Content-Type: application/json" -d \'{"input":"test"}\' 2>/dev/null')
print(f"TTS endpoint status: {out}")

# Step 7: Upload studio page.tsx
print("\nUploading AI Hub Studio page.tsx...")
def upload(local, remote):
    remote_dir = os.path.dirname(remote).replace("\\", "/")
    run(f'mkdir -p "{remote_dir}"')
    sftp = ssh.open_sftp()
    sftp.put(local, remote)
    sftp.close()

studio_file = os.path.join(BASE, "ai-hub-studio", "src", "app", "page.tsx")
if os.path.exists(studio_file):
    upload(studio_file, "/mnt/seagate/ai-hub-studio/src/app/page.tsx")
    print("page.tsx uploaded")

# Step 8: Rebuild studio
print("\nRebuilding AI Hub Studio...")
out, err = run('cd /mnt/seagate/ai-hub-studio && python deploy.py 2>&1 | tail -10', timeout=300)
print(f"Studio deploy: {out}")

ssh.close()
print("\n=== ALL DONE ===")
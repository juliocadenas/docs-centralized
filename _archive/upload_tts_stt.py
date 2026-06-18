"""Upload TTS/STT services to NAB9"""
import paramiko, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

TTS_CODE = r'''
import http.server
import os, json

HAVE_TTS = False
try:
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
    HAVE_TTS = True
except Exception as e:
    print(f"TTS not ready: {e}")

HTML_ONLINE = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>XTTS-v2 - AI Hub Madrid</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Segoe UI,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:2.5rem;max-width:480px;width:100%;text-align:center}
.icon{font-size:4rem;margin-bottom:1rem}
h1{font-size:1.8rem;font-weight:800;color:#fff;margin-bottom:.5rem}
.badge{display:inline-block;background:rgba(16,185,129,.15);color:#10b981;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1.2rem}
textarea,input{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:.9rem;color:#fff;font-size:.9rem;width:100%;resize:vertical;margin:.5rem 0}
textarea:focus,input:focus{outline:none;border-color:#6366f1}
button{background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;color:#fff;padding:.9rem;border-radius:12px;font-weight:700;font-size:.95rem;cursor:pointer;width:100%}
p{color:#9ca3af;line-height:1.6}
a{color:#6366f1}
.footer{margin-top:2rem;font-size:.75rem;color:#4b5563}
</style></head>
<body><div class="card">
<div class="icon">🎙️</div>
<h1>XTTS-v2</h1>
<div class="badge">ONLINE - Listo para usar</div>
<p>Text-to-Speech multilingue. Convierte texto a voz natural en multiples idiomas.</p>
<form action="/speak" method="post" enctype="multipart/form-data" style="margin-top:1rem">
<textarea name="text" rows="4" placeholder="Escribe el texto a convertir en voz..." required></textarea>
<button type="submit">Generar Voz</button>
</form>
<div class="footer">AI Hub Madrid &middot; <a href="http://100.105.27.27:3000">Volver al Hub</a></div>
</div></body></html>"""

HTML_INSTALLING = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>XTTS-v2 - AI Hub Madrid</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Segoe UI,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:2.5rem;max-width:480px;width:100%;text-align:center}
.icon{font-size:4rem;margin-bottom:1rem}
h1{font-size:1.8rem;font-weight:800;color:#fff;margin-bottom:.5rem}
.badge{display:inline-block;background:rgba(245,158,11,.15);color:#f59e0b;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1.2rem}
p{color:#9ca3af;line-height:1.6}
a{color:#6366f1}
.footer{margin-top:2rem;font-size:.75rem;color:#4b5563}
</style></head>
<body><div class="card">
<div class="icon">🎙️</div>
<h1>XTTS-v2</h1>
<div class="badge">Instalando en el servidor</div>
<p>Text-to-Speech multilingue. Convierte texto a voz natural.</p>
<p style="margin-top:1.5rem;color:#f59e0b">Descargando modelo (~3GB). Disponible proximamente.</p>
<div class="footer">AI Hub Madrid &middot; <a href="http://100.105.27.27:3000">Volver al Hub</a></div>
</div></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write((HTML_ONLINE if HAVE_TTS else HTML_INSTALLING).encode())

    def do_POST(self):
        if not HAVE_TTS:
            self.send_response(503); self.end_headers(); return
        cl = int(self.headers.get("Content-Length",0))
        body = self.rfile.read(cl).decode()
        text = body.split("text=")[1].split("&")[0] if "text=" in body else ""
        text = __import__("urllib.parse").unquote_plus(text).strip()
        if not text:
            self.send_response(400); self.end_headers(); return

        out_path = f"/tmp/tts_{abs(hash(text))}.wav"
        tts.tts_to_file(text=text, file_path=out_path, speaker="Ana", language="es")
        with open(out_path,"rb") as f:
            audio_data = f.read()
        
        self.send_response(200)
        self.send_header("Content-type","audio/wav")
        self.send_header("Content-Length",str(len(audio_data)))
        self.end_headers()
        self.wfile.write(audio_data)

http.server.ThreadingHTTPServer(("0.0.0.0",8010), Handler).serve_forever()
'''

STT_CODE = r'''
import http.server

HTML_INSTALLING = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Whisper v3 - AI Hub Madrid</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Segoe UI,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:2.5rem;max-width:480px;width:100%;text-align:center}
.icon{font-size:4rem;margin-bottom:1rem}
h1{font-size:1.8rem;font-weight:800;color:#fff;margin-bottom:.5rem}
.badge{display:inline-block;background:rgba(245,158,11,.15);color:#f59e0b;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1.2rem}
p{color:#9ca3af;line-height:1.6}
a{color:#6366f1}
.footer{margin-top:2rem;font-size:.75rem;color:#4b5563}
</style></head>
<body><div class="card">
<div class="icon">🎤</div>
<h1>Whisper large-v3</h1>
<div class="badge">Instalando en el servidor</div>
<p>Speech-to-Text de OpenAI. Transcribe audio a texto en 100+ idiomas.</p>
<p style="margin-top:1.5rem;color:#f59e0b">Descargando modelo (~3GB). Disponible proximamente.</p>
<div class="footer">AI Hub Madrid &middot; <a href="http://100.105.27.27:3000">Volver al Hub</a></div>
</div></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_INSTALLING.encode())

http.server.ThreadingHTTPServer(("0.0.0.0",8020), Handler).serve_forever()
'''


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=20)

    # Write TTS code directly via heredoc
    stdin, stdout, stderr = c.exec_command(f"cat > /tmp/tts_svc.py << 'EOF'\n{TTS_CODE}\nEOF", timeout=10)
    err = stderr.read().decode()
    print("TTS upload:", "OK" if not err else f"ERR:{err[:100]}")

    stdin, stdout, stderr = c.exec_command(f"cat > /tmp/stt_svc.py << 'EOF'\n{STT_CODE}\nEOF", timeout=10)
    err = stderr.read().decode()
    print("STT upload:", "OK" if not err else f"ERR:{err[:100]}")

    # Kill old and start
    c.exec_command("pkill -f 'tts_svc.py|stt_svc.py' 2>/dev/null; sleep 1; true", timeout=5)
    c.exec_command("nohup python3 /tmp/tts_svc.py > /tmp/tts_svc.log 2>&1 &", timeout=5)
    c.exec_command("nohup python3 /tmp/stt_svc.py > /tmp/stt_svc.log 2>&1 &", timeout=5)
    time.sleep(4)

    # Verify
    for port, name in [(8010, "TTS"), (8020, "STT")]:
        stdin, stdout, stderr = c.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}", timeout=5)
        print(f"{name} :{port} -> HTTP {stdout.read().decode().strip()}")

    c.close()

if __name__ == "__main__":
    main()
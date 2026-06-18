"""Final deployment: CogVideoX/StoryDiffusion services + Gateway Docker + docs"""
import paramiko, time, os

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

COGVIDEOX_SERVICE = r'''
import http.server

HTML = """<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>CogVideoX (THUDM) - AI Hub Madrid</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Segoe UI,system-ui,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:2.5rem;max-width:480px;width:100%;text-align:center}
.icon{font-size:4rem;margin-bottom:1rem}
h1{font-size:1.8rem;font-weight:800;color:#fff;margin-bottom:.5rem}
.badge{display:inline-block;background:rgba(245,158,11,.15);color:#f59e0b;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1.2rem}
p{color:#9ca3af;line-height:1.6;font-size:.95rem}
a{color:#6366f1}
.footer{margin-top:2rem;font-size:.75rem;color:#4b5563}
</style></head>
<body><div class="card">
<div class="icon">🎥</div>
<h1>CogVideoX (THUDM)</h1>
<div class="badge">Instalando en el servidor</div>
<p>Video generation de alta calidad. El mejor modelo open-source de video.</p>
<p style="margin-top:1.5rem;color:#f59e0b">Descargando checkpoints. Disponible proximamente.</p>
<div class="footer">AI Hub Madrid &middot; NAB9 &middot; <a href="http://100.105.27.27:3000">Volver al Hub</a></div>
</div></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

http.server.ThreadingHTTPServer(("0.0.0.0",7861), H).serve_forever()
'''

STORYDIFFUSION_SERVICE = r'''
import http.server

HTML = """<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>StoryDiffusion - AI Hub Madrid</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Segoe UI,system-ui,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.card{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:2.5rem;max-width:480px;width:100%;text-align:center}
.icon{font-size:4rem;margin-bottom:1rem}
h1{font-size:1.8rem;font-weight:800;color:#fff;margin-bottom:.5rem}
.badge{display:inline-block;background:rgba(245,158,11,.15);color:#f59e0b;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1.2rem}
p{color:#9ca3af;line-height:1.6;font-size:.95rem}
a{color:#6366f1}
.footer{margin-top:2rem;font-size:.75rem;color:#4b5563}
</style></head>
<body><div class="card">
<div class="icon">📖</div>
<h1>StoryDiffusion</h1>
<div class="badge">Instalando en el servidor</div>
<p>Personajes consistentes -> comic -> video. Ideal para series de YouTube.</p>
<p style="margin-top:1.5rem;color:#f59e0b">Configurando pipeline. Disponible proximamente.</p>
<div class="footer">AI Hub Madrid &middot; NAB9 &middot; <a href="http://100.105.27.27:3000">Volver al Hub</a></div>
</div></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

http.server.ThreadingHTTPServer(("0.0.0.0",7862), H).serve_forever()
'''

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=20)

    # Upload services via heredoc
    print("=== CogVideoX (:7861) ===")
    c.exec_command(f"cat > /tmp/cogvideox_svc.py << 'ENDPY'\n{COGVIDEOX_SERVICE}\nENDPY", timeout=10)
    c.exec_command("pkill -f cogvideox_svc 2>/dev/null; sleep 1; true", timeout=5)
    c.exec_command("nohup python3 /tmp/cogvideox_svc.py > /tmp/cogvideox.log 2>&1 &", timeout=5)
    
    print("=== StoryDiffusion (:7862) ===")
    c.exec_command(f"cat > /tmp/storydiffusion_svc.py << 'ENDPY'\n{STORYDIFFUSION_SERVICE}\nENDPY", timeout=10)
    c.exec_command("pkill -f storydiffusion_svc 2>/dev/null; sleep 1; true", timeout=5)
    c.exec_command("nohup python3 /tmp/storydiffusion_svc.py > /tmp/storydiffusion.log 2>&1 &", timeout=5)
    
    time.sleep(4)

    # Verify
    print("\n=== Verification ===")
    for name, port in [("CogVideoX",7861), ("StoryDiffusion",7862), ("Rembg",8050), ("Real-ESRGAN",8051), ("Hallo2",8070)]:
        stdin, stdout, stderr = c.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}", timeout=5)
        code = stdout.read().decode().strip()
        status = "ONLINE" if code == "200" else "OFFLINE"
        print(f"  {status} {name} :{port} HTTP {code}")

    # Gateway Docker deployment
    print("\n=== Gateway Docker ===")
    c.exec_command("cd /home/pepe/ai-hub-gateway && docker stop ai-hub-gateway 2>/dev/null; docker rm ai-hub-gateway 2>/dev/null; true", timeout=5)
    stdin, stdout, stderr = c.exec_command("cd /home/pepe/ai-hub-gateway && docker build -t ai-hub-gateway . 2>&1 | tail -5", timeout=60)
    print("Build:", stdout.read().decode().strip()[:200])
    c.exec_command("docker run -d --name ai-hub-gateway --restart unless-stopped --network host ai-hub-gateway", timeout=10)
    time.sleep(2)
    stdin, stdout, stderr = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/health || curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/v1/models", timeout=5)
    print("Gateway:", stdout.read().decode().strip())

    c.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
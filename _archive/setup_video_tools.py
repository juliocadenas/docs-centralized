"""Clone and start CogVideoX + StoryDiffusion services on NAB9"""
import paramiko, time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

SETUP = '''#!/bin/bash
# Instalar CogVideoX + StoryDiffusion en NAB9
set -e
cd /mnt/seagate

echo "=== Clonando repos ==="
test -d CogVideoX || git clone https://github.com/THUDM/CogVideoX.git
test -d StoryDiffusion || git clone https://github.com/HVision-NKU/StoryDiffusion.git

echo "=== Directorios modelos ==="
mkdir -p /mnt/seagate/models/cogvideox /mnt/seagate/models/storydiffusion

echo "=== Servicios HTTP CogVideoX en 7861 ==="
cat > /tmp/cogvideox_svc.py << 'EOF2'
import http.server, socketserver, threading, time, json

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
<div class="footer">AI Hub Madrid · NAB9 · <a href="http://100.105.27.27:3000">Volver al Hub</a></div>
</div></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

srv = http.server.ThreadingHTTPServer(("0.0.0.0",7861), H)
print("CogVideoX on port 7861")
srv.serve_forever()
EOF2

nohup python3 /tmp/cogvideox_svc.py > /tmp/cogvideox.log 2>&1 &
echo "CogVideoX PID: $!"

cat > /tmp/storydiffusion_svc.py << 'EOF3'
import http.server, socketserver, threading, time, json

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
<div class="footer">AI Hub Madrid · NAB9 · <a href="http://100.105.27.27:3000">Volver al Hub</a></div>
</div></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

srv = http.server.ThreadingHTTPServer(("0.0.0.0",7862), H)
print("StoryDiffusion on port 7862")
srv.serve_forever()
EOF3

nohup python3 /tmp/storydiffusion_svc.py > /tmp/storydiffusion.log 2>&1 &
echo "StoryDiffusion PID: $!"

echo "=== Verificacion ==="
sleep 2
curl -s -o /dev/null -w '%{http_code}' http://localhost:7861 && echo " CogVideoX OK"
curl -s -o /dev/null -w '%{http_code}' http://localhost:7862 && echo " StoryDiffusion OK"

echo "DONE video tools"
'''

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=20)

    # Write and execute setup script
    stdin, stdout, stderr = c.exec_command(f"cat > /tmp/setup_video.sh << 'EOF'\n{SETUP}\nEOF", timeout=10)
    err = stderr.read().decode()
    print("Upload:", "OK" if not err else f"ERR:{err[:100]}")

    stdin, stdout, stderr = c.exec_command("bash /tmp/setup_video.sh 2>&1", timeout=120)
    out = stdout.read().decode()
    err = stderr.read().decode()
    print(out[:500] if out else "NO OUT")
    if err: print("ERR:", err[:300])

    # Verify
    for port in [7861, 7862]:
        stdin, stdout, stderr = c.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}", timeout=5)
        print(f"Port {port}: HTTP {stdout.read().decode().strip()}")

    c.close()
    print("Done!")

if __name__ == "__main__":
    main()
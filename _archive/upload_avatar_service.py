"""Upload and start avatar HTTP services on NAB9"""
import paramiko, time, os

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

SCRIPT = r'''
import http.server, socketserver, threading

PAGES = {
    8070: ("Hallo2", "🎭", "Sube foto + audio = video del avatar hablando. Equivalente a HeyGen."),
    8043: ("LatentSync", "👄", "Sincronizacion de labios perfecta con difusion. Equivalente a HeyGen Lip-sync."),
    8044: ("LivePortrait", "🖼️", "Anima fotos con expresiones faciales naturales. Equivalente a HeyGen Express."),
    8040: ("MuseTalk", "🗣️", "Lip-sync en tiempo real. Pipeline avatar hablando. Equivalente a HeyGen Live."),
}

HTML = """<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>{name} - AI Hub Madrid</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Segoe UI,system-ui,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}}
.card{{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:2.5rem;max-width:480px;width:100%;text-align:center}}
.icon{{font-size:4rem;margin-bottom:1rem}}
h1{{font-size:1.8rem;font-weight:800;color:#fff;margin-bottom:.5rem}}
.badge{{display:inline-block;background:rgba(245,158,11,.15);color:#f59e0b;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1.2rem}}
p{{color:#9ca3af;line-height:1.6;font-size:.95rem}}
a{{color:#6366f1}}
.footer{{margin-top:2rem;font-size:.75rem;color:#4b5563}}
</style></head>
<body><div class="card">
<div class="icon">{icon}</div>
<h1>{name}</h1>
<div class="badge">Instalando en el servidor</div>
<p>{desc}</p>
<p style="margin-top:1.5rem">Los checkpoints se estan descargando. Disponible proximamente.</p>
<div class="footer">AI Hub Madrid &middot; NAB9 &middot; RTX 5080 16GB &middot; <a href="http://100.105.27.27:3000">Volver al Hub</a></div>
</div></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(self.server.page.encode())

def serve(port, name, icon, desc):
    srv = http.server.ThreadingHTTPServer(("0.0.0.0",port), Handler)
    srv.page = HTML.format(name=name, icon=icon, desc=desc)
    print(f"{name} -> port {port}")
    srv.serve_forever()

for port, (name, icon, desc) in PAGES.items():
    threading.Thread(target=serve, args=(port,name,icon,desc), daemon=True).start()

print("All 4 avatar services running on ports 8070, 8043, 8044, 8040")
import time
while True:
    time.sleep(60)
'''

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=20)
    
    # Write script
    stdin, stdout, stderr = c.exec_command(f"cat > /tmp/serve_avatars.py << 'ENDOFPYTHON'\n{SCRIPT}\nENDOFPYTHON", timeout=10)
    out = stdout.read().decode()
    err = stderr.read().decode()
    print("Write:", "OK" if not err else f"ERR:{err[:100]}")
    
    # Kill old
    stdin, stdout, stderr = c.exec_command("pkill -f serve_avatars 2>/dev/null; sleep 1; true", timeout=5)
    
    # Start
    stdin, stdout, stderr = c.exec_command("nohup python3 /tmp/serve_avatars.py > /tmp/serve_avatars.log 2>&1 & echo PID=$!", timeout=5)
    print("Start:", stdout.read().decode().strip())
    time.sleep(3)
    
    # Verify
    for port in [8070, 8043, 8044, 8040]:
        stdin, stdout, stderr = c.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}", timeout=5)
        code = stdout.read().decode().strip()
        print(f"Port {port}: HTTP {code}")
    
    c.close()
    print("Done!")

if __name__ == "__main__":
    main()
"""Servicios de Efectos - Rembg, Real-ESRGAN, Higgsfield"""
import os, sys, threading, time, io, base64, json
from http.server import HTTPServer, BaseHTTPRequestHandler

PAGES = {
    8050: {
        "name": "Rembg - Quitar Fondo",
        "icon": "✂️",
        "desc": "Sube una imagen y elimina el fondo automaticamente. Equivalente a Remove.bg.",
        "status": "installing",
    },
    8051: {
        "name": "Real-ESRGAN - Upscaler 4x",
        "icon": "🔍",
        "desc": "Mejora la resolucion de imagenes hasta 4x con IA. Equivalente a Upscale.media.",
        "status": "installing",
    },
    8052: {
        "name": "Higgsfield AI - Efectos",
        "icon": "⚡",
        "desc": "Efectos de video, motion control y camara. Equivalente a Higgsfield AI.",
        "status": "installing",
    },
}

# Instalar dependencias
try:
    from rembg import remove
    from PIL import Image
    PAGES[8050]["status"] = "online"
except:
    pass

try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    PAGES[8051]["status"] = "online"
except:
    pass

HTML = """<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>{name} - AI Hub Madrid</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Segoe UI,system-ui,sans-serif;background:#0f0f1a;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}}
.card{{background:#1a1a2e;border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:2.5rem;max-width:480px;width:100%;text-align:center}}
.icon{{font-size:4rem;margin-bottom:1rem}}
h1{{font-size:1.8rem;font-weight:800;color:#fff;margin-bottom:.5rem}}
.badge{{display:inline-block;padding:.4rem 1.2rem;border-radius:20px;font-size:.85rem;font-weight:600;margin-bottom:1.2rem}}
.badge.installing{{background:rgba(245,158,11,.15);color:#f59e0b}}
.badge.online{{background:rgba(16,185,129,.15);color:#10b981}}
p{{color:#9ca3af;line-height:1.6;font-size:.95rem}}
input[type=file]{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:.9rem;color:#fff;font-size:.9rem;width:100%;margin:1rem 0}}
input[type=file]::file-selector-button{{background:#6366f1;border:none;color:#fff;padding:.5rem 1rem;border-radius:8px;cursor:pointer;margin-right:.5rem}}
button{{background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;color:#fff;padding:.9rem;border-radius:12px;font-weight:700;font-size:.95rem;cursor:pointer;width:100%;transition:opacity .2s}}
button:hover{{opacity:.85}}
a{{color:#6366f1}}
.footer{{margin-top:2rem;font-size:.75rem;color:#4b5563}}
img{{max-width:100%;border-radius:12px;margin-top:1rem}}
</style></head>
<body><div class="card">
<div class="icon">{icon}</div>
<h1>{name}</h1>
<div class="badge {status}">{status_text}</div>
<p>{desc}</p>
{content}
<div class="footer">AI Hub Madrid &middot; NAB9 &middot; <a href="http://100.105.27.27:3000">Volver al Hub</a></div>
</div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        config = self.server.config
        status = config["status"]
        status_text = "ONLINE - Listo para usar" if status == "online" else "Instalando en el servidor"
        
        if status == "online":
            content = '<form action="/process" method="post" enctype="multipart/form-data"><input type="file" name="file" accept="image/*" required><button type="submit">Procesar</button></form>'
        else:
            content = '<p style="margin-top:1.5rem">Instalando dependencias. Disponible proximamente.</p>'
        
        page = HTML.format(name=config["name"], icon=config["icon"], status=config["status"],
                          status_text=status_text, desc=config["desc"], content=content)
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode())
    
    def do_POST(self):
        config = self.server.config
        if config["status"] != "online":
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"<h1>Servicio no disponible</h1>")
            return
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Parsear multipart
        result_html = "<p>Procesando...</p>"
        
        try:
            from rembg import remove
            from PIL import Image
            import io
            
            # Extraer imagen del form data
            boundary = self.headers.get('Content-Type', '').split('boundary=')[-1].encode()
            parts = body.split(b'--' + boundary)
            for part in parts:
                if b'Content-Type: image' in part:
                    header_end = part.find(b'\r\n\r\n')
                    img_data = part[header_end+4:].rstrip(b'\r\n--')
                    img = Image.open(io.BytesIO(img_data))
                    result = remove(img)
                    buf = io.BytesIO()
                    result.save(buf, format='PNG')
                    img_b64 = base64.b64encode(buf.getvalue()).decode()
                    result_html = f'<img src="data:image/png;base64,{img_b64}" alt="Resultado"><br><a href="data:image/png;base64,{img_b64}" download="sin_fondo.png">Descargar</a>'
                    break
        except Exception as e:
            result_html = f'<p style="color:#ef4444">Error: {e}</p>'
        
        page = HTML.format(name=config["name"], icon=config["icon"], status=config["status"],
                          status_text="ONLINE", desc=config["desc"], content=result_html + '<p><a href="/">Nueva imagen</a></p>')
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode())


def serve(port, config):
    srv = HTTPServer(("0.0.0.0", port), Handler)
    srv.config = config
    print(f"{config['name']} -> port {port}")
    srv.serve_forever()


if __name__ == "__main__":
    for port, config in PAGES.items():
        threading.Thread(target=serve, args=(port, config), daemon=True).start()
    print("Effects services running on ports 8050, 8051, 8052")
    while True:
        time.sleep(60)
#!/usr/bin/env python3
"""Deploy avatar services to NAB9 - Hallo2, LatentSync, LivePortrait, MuseTalk."""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '100.105.27.27'
USER = 'pepe'
PASS = 'pepe1234'

def main():
    print("=== DEPLOY AVATAR SERVICES ===\n")

    # 1. Connect
    print("[1/6] Conectando al servidor...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    print("      ✅ Conectado")

    def run(cmd, timeout=120, check=True):
        print(f"      $ {cmd[:80]}")
        _, o, e = ssh.exec_command(cmd, timeout=timeout)
        o.channel.recv_exit_status()
        out = o.read().decode('utf-8', 'replace').strip()
        err = e.read().decode('utf-8', 'replace').strip()
        return out, err

    # 2. Upload avatar_services.py
    print("\n[2/6] Subiendo avatar_services.py...")
    sftp = ssh.open_sftp()
    sftp.put('avatar_services.py', '/home/pepe/avatar_services.py')
    sftp.chmod('/home/pepe/avatar_services.py', 0o755)
    print("      ✅ Subido a /home/pepe/avatar_services.py")
    sftp.close()

    # 3. Fix numpy + install opencv
    print("\n[3/6] Instalando dependencias (numpy, opencv, imageio)...")
    out, err = run('/home/pepe/ai_env/bin/pip install "numpy<2" opencv-python-headless imageio imageio-ffmpeg 2>&1 | tail -5', timeout=300)
    print(f"      {out}")

    # 4. Verify deps
    print("\n[4/6] Verificando dependencias...")
    for mod in ['numpy', 'cv2', 'imageio']:
        out, _ = run(f'/home/pepe/ai_env/bin/python -c "import {mod}; print({mod}.__version__)" 2>&1')
        print(f"      {mod}: {out}")

    # 5. Create systemd service
    print("\n[5/6] Creando servicio systemd...")
    service = """[Unit]
Description=Avatar AI Services (Hallo2, LatentSync, LivePortrait, MuseTalk)
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/home/pepe
ExecStart=/home/pepe/ai_env/bin/python /home/pepe/avatar_services.py
Restart=always
RestartSec=10
Environment=HOME=/home/pepe
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/avatar_services.service', 'w') as f:
        f.write(service)
    sftp.close()

    run('echo "pepe1234" | sudo -S cp /tmp/avatar_services.service /etc/systemd/system/avatar_services.service 2>/dev/null', check=False)
    run('echo "pepe1234" | sudo -S systemctl daemon-reload 2>/dev/null', check=False)
    run('echo "pepe1234" | sudo -S systemctl enable avatar_services 2>/dev/null', check=False)
    run('echo "pepe1234" | sudo -S systemctl restart avatar_services 2>/dev/null', check=False)
    print("      ✅ Servicio creado e iniciado")

    # 6. Verify
    print("\n[6/6] Verificando servicios...")
    time.sleep(5)  # Wait for uvicorn to start
    for name, port in [("Hallo2", 8070), ("LatentSync", 8043), ("LivePortrait", 8044), ("MuseTalk", 8040)]:
        out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{port}/ 2>/dev/null', check=False)
        status = "✅ ONLINE" if out == "200" else f"❌ HTTP {out}"
        print(f"      {name} :{port}: {status}")

    # Check service status
    out, _ = run('echo "pepe1234" | sudo -S systemctl is-active avatar_services 2>/dev/null', check=False)
    print(f"\n      Systemd status: {out}")

    ssh.close()
    print("\n=== DEPLOY COMPLETADO ===")

if __name__ == '__main__':
    main()
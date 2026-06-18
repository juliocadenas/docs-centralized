#!/usr/bin/env python3
"""Deploy effects services to NAB9 - Rembg, Real-ESRGAN, Higgsfield."""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '100.105.27.27'
USER = 'pepe'
PASS = 'pepe1234'

def main():
    print("=== DEPLOY EFFECTS SERVICES ===\n")

    print("[1/6] Conectando...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    print("      Connected")

    def run(cmd, timeout=300):
        _, o, e = ssh.exec_command(cmd, timeout=timeout)
        o.channel.recv_exit_status()
        return o.read().decode('utf-8', 'replace').strip(), e.read().decode('utf-8', 'replace').strip()

    # Upload effects_services.py
    print("\n[2/6] Subiendo effects_services.py...")
    sftp = ssh.open_sftp()
    sftp.put('effects_services.py', '/home/pepe/effects_services.py')
    sftp.chmod('/home/pepe/effects_services.py', 0o755)
    sftp.close()
    print("      Done")

    # Install rembg
    print("\n[3/6] Instalando rembg...")
    out, err = run('/home/pepe/ai_env/bin/pip install rembg onnxruntime 2>&1 | tail -5', timeout=300)
    print(f"      {out}")

    # Install realesrgan
    print("\n[4/6] Instalando realesrgan + basicsr...")
    out, err = run('/home/pepe/ai_env/bin/pip install realesrgan basicsr 2>&1 | tail -5', timeout=300)
    print(f"      {out}")

    # Verify imports
    print("\n[5/6] Verificando imports...")
    out, _ = run('/home/pepe/ai_env/bin/python -c "from rembg import remove; print(\'rembg OK\')" 2>&1')
    print(f"      rembg: {out}")
    out, _ = run('/home/pepe/ai_env/bin/python -c "from basicsr.archs.rrdbnet_arch import RRDBNet; print(\'basicsr OK\')" 2>&1')
    print(f"      basicsr: {out}")

    # Create systemd service
    print("\n[6/6] Creando servicio systemd...")
    service = """[Unit]
Description=Effects Services (Rembg, Real-ESRGAN, Higgsfield)
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/home/pepe
ExecStart=/home/pepe/ai_env/bin/python /home/pepe/effects_services.py
Restart=always
RestartSec=10
Environment=HOME=/home/pepe
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/effects_services.service', 'w') as f:
        f.write(service)
    sftp.close()

    run('echo "pepe1234" | sudo -S cp /tmp/effects_services.service /etc/systemd/system/effects_services.service 2>/dev/null')
    run('echo "pepe1234" | sudo -S systemctl daemon-reload 2>/dev/null')
    run('echo "pepe1234" | sudo -S systemctl enable effects_services 2>/dev/null')
    run('echo "pepe1234" | sudo -S systemctl restart effects_services 2>/dev/null')
    print("      Service created")

    # Verify
    time.sleep(3)
    print("\n=== Verificacion ===")
    for name, port in [("Rembg", 8050), ("Real-ESRGAN", 8051), ("Higgsfield", 8052)]:
        out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{port}/ 2>/dev/null')
        status = "ONLINE" if out == "200" else f"HTTP {out}"
        print(f"  {name} :{port}: {status}")

    out, _ = run('echo "pepe1234" | sudo -S systemctl is-active effects_services 2>/dev/null')
    print(f"  Systemd: {out}")

    ssh.close()
    print("\n=== DONE ===")

if __name__ == '__main__':
    main()
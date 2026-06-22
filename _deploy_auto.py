"""
Deploy automático al NAB9 via SSH (paramiko).
Usuario: pepe / pepe1234
"""
import os
import sys
import io
import paramiko
import time

# Fix Windows console encoding (CP1252 doesn't support emojis)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuración
HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
LOCAL_FILE = os.path.join(os.path.dirname(__file__), "ai-hub-deploy.tar.gz")
REMOTE_FILE = "/tmp/ai-hub-deploy.tar.gz"

def progress(transferred, total):
    pct = (transferred / total) * 100 if total > 0 else 0
    sys.stdout.write(f"\r  Subiendo: {transferred//1024}KB / {total//1024}KB ({pct:.0f}%)")
    sys.stdout.flush()

def run_command(ssh, cmd, timeout=120):
    """Ejecutar comando SSH y mostrar output en tiempo real."""
    print(f"\n  $ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        for line in out.split('\n'):
            print(f"    {line}")
    if err:
        for line in err.split('\n'):
            print(f"    [stderr] {line}")
    return exit_code, out, err

def main():
    if not os.path.exists(LOCAL_FILE):
        print(f"ERROR: No existe {LOCAL_FILE}")
        print("Ejecuta primero: python _pack.py")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"  DEPLOY AI HUB GATEWAY v2.1.1 -> NAB9")
    print(f"  Host: {HOST} | User: {USER}")
    print(f"{'='*60}")

    # 1. Conectar SSH
    print("\n[1/5] Conectando via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USER, password=PASS, timeout=15)
        print("  ✅ Conexión SSH establecida")
    except Exception as e:
        print(f"  ❌ Error conectando: {e}")
        sys.exit(1)

    # 2. Subir paquete via SFTP
    print(f"\n[2/5] Subiendo ai-hub-deploy.tar.gz...")
    sftp = ssh.open_sftp()
    try:
        sftp.put(LOCAL_FILE, REMOTE_FILE, callback=progress)
        print(f"\n  ✅ Archivo subido ({os.path.getsize(LOCAL_FILE)//1024}KB)")
    except Exception as e:
        print(f"\n  ❌ Error subiendo: {e}")
        ssh.close()
        sys.exit(1)
    finally:
        sftp.close()

    # 3. Descomprimir
    print(f"\n[3/5] Descomprimiendo en servidor...")
    code, _, _ = run_command(ssh, "cd /tmp && rm -rf ai-hub-gateway ai-hub-deploy && mkdir -p ai-hub-deploy && tar xzf ai-hub-deploy.tar.gz -C ai-hub-deploy")
    if code != 0:
        print("  ❌ Error descomprimiendo")
        ssh.close()
        sys.exit(1)
    print("  ✅ Descomprimido")

    # 4. Ejecutar deploy (con sudo -S para inyectar password)
    print(f"\n[4/5] Ejecutando deploy...")
    # Dar permisos sudo sin TTY: echo password | sudo -S
    deploy_cmd = f'echo "{PASS}" | sudo -S bash -c "cd /tmp/ai-hub-deploy && export SUDO_PASS={PASS} && bash _deploy_on_server.sh"'
    code, out, err = run_command(ssh, deploy_cmd, timeout=300)
    if code != 0:
        print(f"  ⚠️ Deploy terminó con código {code}")
    else:
        print("  ✅ Deploy completado")

    # 5. Verificar Gateway
    print(f"\n[5/5] Verificando Gateway...")
    time.sleep(3)
    code, out, _ = run_command(ssh, "curl -s http://localhost:9000/v1/status | head -c 500")
    if "online" in out.lower() or "status" in out.lower():
        print("\n  ✅ Gateway respondiendo en http://100.105.27.27:9000")
    else:
        print("\n  ⚠️ Gateway no responde aún (puede estar iniciando)")

    # Verificar Ollama y modelos
    print(f"\n[bonus] Verificando Ollama y modelos...")
    code, out, _ = run_command(ssh, "curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c \"import sys,json; data=json.load(sys.stdin); [print(f'  - {m[\\\"name\\\"]}') for m in data.get('models',[])]\" 2>/dev/null")

    # Cleanup
    run_command(ssh, "rm -f /tmp/ai-hub-deploy.tar.gz")

    ssh.close()
    print(f"\n{'='*60}")
    print(f"  DEPLOY COMPLETADO")
    print(f"  Gateway: http://100.105.27.27:9000")
    print(f"  Docs:    http://100.105.27.27:9000/docs")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
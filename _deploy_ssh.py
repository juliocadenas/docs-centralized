#!/usr/bin/env python3
"""
Deploy Gateway al NAB9 via SSH con password.
Usa paramiko para conexión SSH interactiva.
"""
import getpass
import paramiko
import os
import sys
import io

# Configuración
HOST = "100.105.27.27"
USER = "pepe"
GATEWAY_DIR = "/mnt/seagate/api/ai-hub-gateway"
REPO_DIR = "/mnt/seagate/api/IA-HUB-MADRID1"

# Archivos a copiar
FILES_TO_COPY = [
    # Routers
    ("ai-hub-gateway/gateway/routers/status.py",   f"{GATEWAY_DIR}/gateway/routers/status.py"),
    ("ai-hub-gateway/gateway/routers/voice.py",    f"{GATEWAY_DIR}/gateway/routers/voice.py"),
    ("ai-hub-gateway/gateway/routers/effects.py",  f"{GATEWAY_DIR}/gateway/routers/effects.py"),
    ("ai-hub-gateway/gateway/routers/avatar.py",   f"{GATEWAY_DIR}/gateway/routers/avatar.py"),
    ("ai-hub-gateway/gateway/routers/llm.py",      f"{GATEWAY_DIR}/gateway/routers/llm.py"),
    # Config
    ("ai-hub-gateway/gateway/config.py",           f"{GATEWAY_DIR}/gateway/config.py"),
    # Docker compose
    ("ai-hub-gateway/docker-compose.yml",          f"{GATEWAY_DIR}/docker-compose.yml"),
]

# Directorios a copiar (recursivo)
DIRS_TO_COPY = [
    ("ai-hub-gateway/services", f"{GATEWAY_DIR}/services"),
]

# Comandos a ejecutar después de copiar
POST_COMMANDS = [
    "sudo systemctl restart ai-hub-gateway",
    "sleep 3",
    "curl -s http://localhost:9000/v1/status | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\\\"status\\\"]}'); online=[s['name'] for s in d['services'] if s['status']=='online']; offline=[s['name'] for s in d['services'] if s['status']!='online']; print(f'Online ({len(online)}): {online}'); print(f'Offline ({len(offline)}): {offline}')\"",
    "curl -s http://localhost:9000/v1/models | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f'Modelos: {len(d[\\\"data\\\"])}'); [print(f'  {m[\\\"id\\\"]}') for m in d['data']]\"",
]


def deploy():
    print("=" * 60)
    print("  DEPLOY AI HUB GATEWAY → NAB9")
    print("=" * 60)

    # Pedir password
    password = getpass.getpass(f"Password para {USER}@{HOST}: ")

    # Conectar SSH
    print(f"\n[1/5] Conectando a {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USER, password=password, timeout=10)
        print("  ✅ Conectado!")
    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")
        sys.exit(1)

    # Crear directorios
    print("\n[2/5] Creando directorios remotos...")
    for cmd in [
        f"mkdir -p {GATEWAY_DIR}/gateway/routers",
        f"mkdir -p {GATEWAY_DIR}/services",
    ]:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.channel.recv_exit_status()

    # Abrir SFTP
    print("\n[3/5] Copiando archivos...")
    sftp = ssh.open_sftp()

    for local_path, remote_path in FILES_TO_COPY:
        if os.path.exists(local_path):
            print(f"  📤 {local_path} → {remote_path}")
            sftp.put(local_path, remote_path)
        else:
            print(f"  ⚠️  No existe: {local_path}")

    # Copiar directorios recursivamente
    for local_dir, remote_dir in DIRS_TO_COPY:
        if os.path.exists(local_dir):
            print(f"  📁 {local_dir}/ → {remote_dir}/")
            # Listar archivos recursivamente
            for root, dirs, files in os.walk(local_dir):
                rel = os.path.relpath(root, local_dir)
                remote_sub = f"{remote_dir}/{rel}" if rel != "." else remote_dir
                # Crear dir remoto
                try:
                    sftp.stat(remote_sub)
                except FileNotFoundError:
                    parts = remote_sub.split("/")
                    for i in range(1, len(parts) + 1):
                        try:
                            sftp.stat("/".join(parts[:i]))
                        except FileNotFoundError:
                            sftp.mkdir("/".join(parts[:i]))

                for f in files:
                    local_file = os.path.join(root, f)
                    remote_file = f"{remote_sub}/{f}"
                    print(f"    📤 {os.path.relpath(local_file, local_dir)}")
                    sftp.put(local_file, remote_file)

    sftp.close()

    # Ejecutar comandos post-deploy
    print("\n[4/5] Reiniciando gateway...")
    for cmd in POST_COMMANDS:
        print(f"  ▶️  {cmd[:80]}")
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        err = stderr.read().decode()
        if output.strip():
            for line in output.strip().split("\n"):
                print(f"     {line}")
        if err.strip():
            for line in err.strip().split("\n")[:3]:
                print(f"     ⚠️  {line}")

    ssh.close()

    print("\n[5/5] ✅ DEPLOY COMPLETADO!")
    print("=" * 60)
    print(f"  Gateway: http://{HOST}:9000/v1/status")
    print(f"  Docs:    http://{HOST}:9000/docs")
    print("=" * 60)


if __name__ == "__main__":
    deploy()
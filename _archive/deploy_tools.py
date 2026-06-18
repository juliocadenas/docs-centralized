"""Subir apps Gradio a NAB9 e instalar repos"""
import paramiko, os, time, sys

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
VENV = "/home/pepe/comfyui_env/bin"

def ssh_cmd(client, cmd, timeout=120):
    print(f"  > {cmd[:80]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print("  OUT:", out[:300])
    if err: print("  ERR:", err[:300])
    return stdout.channel.recv_exit_status()

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=20)
    sftp = client.open_sftp()

    # 1. Subir archivos locales
    local_base = os.path.dirname(__file__)
    apps = ['hallo2_app.py','latentsync_app.py','liveportrait_app.py','musetalk_app.py']
    print("=== Subiendo apps ===")
    for app in apps:
        lpath = os.path.join(local_base, app)
        rpath = f'/home/pepe/{app}'
        sftp.put(lpath, rpath)
        print(f"  Uploaded {app} -> {rpath}")

    sftp.close()

    # 2. Clonar repos
    print("\n=== Clonando repos ===")
    repos = [
        ('bytedance/LatentSync', 'LatentSync'),
        ('KwaiVGI/LivePortrait', 'LivePortrait'),
        ('TMElyralab/MuseTalk', 'MuseTalk'),
    ]
    for github, folder in repos:
        ssh_cmd(client, f"test -d /mnt/seagate/{folder} || cd /mnt/seagate && git clone https://github.com/{github}.git")

    # 3. Verificar archivos subidos
    print("\n=== Verificando ===")
    ssh_cmd(client, "ls -la /home/pepe/*_app.py")
    ssh_cmd(client, "ls -d /mnt/seagate/LatentSync /mnt/seagate/LivePortrait /mnt/seagate/MuseTalk /mnt/seagate/hallo2")

    # 4. Instalar dependencias
    print("\n=== Instalando dependencias ===")
    for repo in ['LatentSync', 'LivePortrait', 'MuseTalk', 'hallo2']:
        ssh_cmd(client, f"test -f /mnt/seagate/{repo}/requirements.txt && {VENV}/pip install -r /mnt/seagate/{repo}/requirements.txt 2>&1 | tail -3 || echo 'No requirements'")

    # 5. Crear dirs de modelos
    ssh_cmd(client, "mkdir -p /mnt/seagate/models/hallo2 /mnt/seagate/models/latentsync /mnt/seagate/models/liveportrait /mnt/seagate/models/musetalk")

    # 6. Lanzar servicios Gradio
    print("\n=== Lanzando servicios ===")
    ssh_cmd(client, "pkill -f 'hallo2_app' 2>/dev/null; pkill -f 'latentsync_app' 2>/dev/null; pkill -f 'liveportrait_app' 2>/dev/null; pkill -f 'musetalk_app' 2>/dev/null; sleep 1; true")
    
    ssh_cmd(client, f"cd /home/pepe && nohup {VENV}/python hallo2_app.py > /tmp/hallo2.log 2>&1 & echo PID=\$!")
    time.sleep(2)
    ssh_cmd(client, f"cd /home/pepe && nohup {VENV}/python latentsync_app.py > /tmp/latentsync.log 2>&1 & echo PID=\$!")
    time.sleep(2)
    ssh_cmd(client, f"cd /home/pepe && nohup {VENV}/python liveportrait_app.py > /tmp/liveportrait.log 2>&1 & echo PID=\$!")
    time.sleep(2)
    ssh_cmd(client, f"cd /home/pepe && nohup {VENV}/python musetalk_app.py > /tmp/musetalk.log 2>&1 & echo PID=\$!")
    time.sleep(3)

    # 7. Verificar
    print("\n=== Verificacion ===")
    ssh_cmd(client, "ps aux | grep '_app.py' | grep -v grep")
    ssh_cmd(client, "ss -tlnp | grep -E ':(8070|8043|8044|8040)'")
    for p in [8070,8043,8044,8040]:
        ssh_cmd(client, f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{p} || echo 'FAIL'")

    client.close()
    print("\n=== DONE ===")

if __name__ == "__main__":
    main()
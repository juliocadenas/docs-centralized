#!/usr/bin/env python3
"""Fix Piper: binary path + voice download con redirects."""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST, USER, PASS = "100.105.27.27", "pepe", "pepe1234"

def run(ssh, cmd, timeout=120):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)
print("Conectado!\n")

# 1. Encontrar binary piper
print("[1] Buscando piper binary...")
out = run(ssh, "find /home/pepe/piper -name 'piper' -type f 2>/dev/null; ls -la /home/pepe/piper/ 2>&1")
print(f"    {out.strip()}")

# Si esta en subdirectorio, moverlo
run(ssh, "cp /home/pepe/piper/piper /home/pepe/piper/piper_bak 2>/dev/null")
run(ssh, "find /home/pepe/piper -name 'piper' -type f -exec cp {} /home/pepe/piper/piper_main \\; 2>/dev/null")

# Verificar que el binary funciona
out = run(ssh, "file /home/pepe/piper/piper 2>&1; /home/pepe/piper/piper --help 2>&1 | head -5")
print(f"    File type + help: {out.strip()[:200]}")

# Si no funciona, descargar de nuevo con curl
if "not found" in out or "error" in out.lower() or "cannot" in out.lower():
    print("    Binary no funciona, redescargando con curl...")
    run(ssh, "rm -rf /home/pepe/piper && mkdir -p /home/pepe/piper", timeout=30)
    run(ssh, "curl -sL 'https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz' -o /home/pepe/piper/piper.tar.gz 2>&1", timeout=120)
    run(ssh, "cd /home/pepe/piper && tar xzf piper.tar.gz 2>&1", timeout=30)
    out = run(ssh, "find /home/pepe/piper -name 'piper' -type f 2>/dev/null")
    print(f"    Buscado de nuevo: {out.strip()}")

# 2. Descargar voces con curl -L (redirects)
print("\n[2] Descargando voz Sharvard con curl -L...")
model_dir = "/mnt/seagate/models/tts/piper/models"
run(ssh, f"rm -f {model_dir}/es_ES-Sharvard-medium.onnx* 2>/dev/null")

base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/medium/es_ES-Sharvard-medium"
out1 = run(ssh, f"curl -sL '{base_url}.onnx' -o '{model_dir}/es_ES-Sharvard-medium.onnx' 2>&1", timeout=120)
out2 = run(ssh, f"curl -sL '{base_url}.onnx.json' -o '{model_dir}/es_ES-Sharvard-medium.onnx.json' 2>&1", timeout=120)

out = run(ssh, f"ls -lh {model_dir}/ 2>&1")
print(f"    {out.strip()}")

# 3. Actualizar tts_svc.py para buscar piper en cualquier subdirectorio
print("\n[3] Actualizando find_piper()...")
# Leer el archivo actual y modificar
sftp = ssh.open_sftp()
with sftp.file("/home/pepe/tts_svc.py", "r") as f:
    content = f.read().decode('utf-8')

# Reemplazar find_piper con busqueda recursiva
old_find = '''def find_piper():
    global PIPER_CMD
    candidates = [
        "/home/pepe/piper/piper",
        "/usr/local/bin/piper",
        "/usr/bin/piper",
        os.path.expanduser("~/.local/bin/piper"),
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            PIPER_CMD = c
            return True
    return False'''

new_find = '''def find_piper():
    global PIPER_CMD
    import glob as _g
    # Search recursively in piper dir
    matches = _g.glob("/home/pepe/piper/**/piper", recursive=True)
    matches += ["/usr/local/bin/piper", "/usr/bin/piper"]
    for c in matches:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            PIPER_CMD = c
            return True
    return False'''

content = content.replace(old_find, new_find)
with sftp.file("/home/pepe/tts_svc.py", "w") as f:
    f.write(content)
sftp.close()
print("    Actualizado")

# 4. Restart
print("\n[4] Reiniciando TTS...")
run(ssh, "echo pepe1234 | sudo -S systemctl restart tts 2>&1")
time.sleep(5)

status = run(ssh, "systemctl is-active tts").strip()
print(f"    TTS: {status}")

out = run(ssh, "curl -s http://localhost:8010/api/status 2>/dev/null")
print(f"    Status: {out.strip()}")

# 5. Test
print("\n[5] Test generando audio...")
test_cmd = "curl -s -X POST http://localhost:8010/api/tts -F 'text=Hola mundo, esto es una prueba de voz' -F 'voice=es_ES-Sharvard-medium' -o /tmp/test_tts.wav -w '%{http_code}' 2>/dev/null"
out = run(ssh, test_cmd, timeout=60)
print(f"    HTTP: {out.strip()}")

out = run(ssh, "ls -lh /tmp/test_tts.wav 2>/dev/null; file /tmp/test_tts.wav 2>/dev/null")
print(f"    Audio: {out.strip()}")

ssh.close()
print("\nDone!")
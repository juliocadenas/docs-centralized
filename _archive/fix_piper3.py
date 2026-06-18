#!/usr/bin/env python3
"""Fix final: descargar voces Piper correctamente."""
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

# 1. Ver contenido de los archivos de 15 bytes
print("[1] Verificando archivos de voz descargados...")
model_dir = "/mnt/seagate/models/tts/piper/models"
out = run(ssh, f"cat {model_dir}/es_ES-Sharvard-medium.onnx 2>&1")
print(f"    Contenido onnx: [{out.strip()}]")
out = run(ssh, f"cat {model_dir}/es_ES-Sharvard-medium.onnx.json 2>&1")
print(f"    Contenido json: [{out.strip()}]")

# 2. El binary está en /home/pepe/piper/piper/piper (doble piper)
# Simplificar: mover todo al directorio correcto
print("\n[2] Reorganizando piper binary...")
run(ssh, "cp /home/pepe/piper/piper/piper /home/pepe/piper/piper_bin 2>/dev/null")
# Tambien copiar librerias necesarias
run(ssh, "ls -la /home/pepe/piper/piper/ 2>&1")

# 3. Descargar voces correctamente - probar diferentes mirrors
print("\n[3] Descargando voz Sharvard...")
run(ssh, f"rm -f {model_dir}/es_ES-Sharvard-medium.onnx* 2>/dev/null")

# URL correcta de HuggingFace (puede necesitar ?download=true)
urls_onnx = [
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/medium/es_ES-Sharvard-medium.onnx?download=true",
    "https://huggingface.co/rhasspy/piper-voices/resolve/refs%2Fconvert%2Fparquet/es/es_ES/medium/es_ES-Sharvard-medium.onnx",
    "https://github.com/rhasspy/piper-voices/raw/main/es/es_ES/medium/es_ES-Sharvard-medium.onnx",
]

onnx_path = f"{model_dir}/es_ES-Sharvard-medium.onnx"
for url in urls_onnx:
    print(f"    Probando: {url[:80]}...")
    out = run(ssh, f"curl -sL '{url}' -o '{onnx_path}' -w '%{{http_code}}|%{{size_download}}' 2>&1", timeout=120)
    print(f"    Resultado: {out.strip()}")
    # Verificar tamaño
    out = run(ssh, f"ls -lh '{onnx_path}' 2>/dev/null | awk '{{print $5}}'")
    size = out.strip()
    print(f"    Tamaño: {size}")
    if "M" in size or "k" in size:
        print(f"    OK! Voz descargada ({size})")
        break
    else:
        print(f"    Falló, intentando siguiente URL...")
        run(ssh, f"rm -f '{onnx_path}'")

# Si ninguna funcionó, usar wget
out = run(ssh, f"ls -lh '{onnx_path}' 2>/dev/null | awk '{{print $5}}'")
if "M" not in out and "k" not in out:
    print("\n    Probando con wget...")
    run(ssh, f"wget -q 'https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/medium/es_ES-Sharvard-medium.onnx' -O '{onnx_path}' 2>&1", timeout=120)
    out = run(ssh, f"ls -lh '{onnx_path}' 2>/dev/null")
    print(f"    {out.strip()}")

# Descargar JSON (más pequeño)
json_path = f"{model_dir}/es_ES-Sharvard-medium.onnx.json"
json_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/medium/es_ES-Sharvard-medium.onnx.json"
run(ssh, f"curl -sL '{json_url}' -o '{json_path}' 2>&1", timeout=60)

out = run(ssh, f"ls -lh {model_dir}/ 2>&1")
print(f"\n    Archivos finales: {out.strip()}")

# 4. Test directo del binary piper
print("\n[4] Test directo del binary piper...")
piper_bin = "/home/pepe/piper/piper/piper"
echo_cmd = f"echo 'Hola mundo' | {piper_bin} --model '{onnx_path}' --output_file /tmp/piper_test.wav 2>&1"
out = run(ssh, echo_cmd, timeout=30)
print(f"    Output: {out.strip()[:200]}")

out = run(ssh, "ls -lh /tmp/piper_test.wav 2>/dev/null; file /tmp/piper_test.wav 2>/dev/null")
print(f"    Audio: {out.strip()}")

# 5. Restart TTS service
print("\n[5] Reiniciando TTS...")
run(ssh, "echo pepe1234 | sudo -S systemctl restart tts 2>&1")
time.sleep(5)

status = run(ssh, "systemctl is-active tts").strip()
print(f"    TTS: {status}")

# 6. Test via HTTP API
print("\n[6] Test via HTTP API...")
test_cmd = "curl -s -X POST http://localhost:8010/api/tts -F 'text=Hola mundo' -F 'voice=es_ES-Sharvard-medium' -o /tmp/test_tts2.wav -w '%{http_code}' 2>/dev/null"
out = run(ssh, test_cmd, timeout=60)
print(f"    HTTP: {out.strip()}")

out = run(ssh, "ls -lh /tmp/test_tts2.wav 2>/dev/null; file /tmp/test_tts2.wav 2>/dev/null")
print(f"    Audio: {out.strip()}")

# Si falla, ver logs
if "Wave" not in out and "WAVE" not in out:
    print("\n    Logs TTS:")
    out = run(ssh, "echo pepe1234 | sudo -S journalctl -u tts --no-pager -n 20 2>&1")
    print(f"    {out.strip()[-500:]}")

# STT
print("\n[7] STT status...")
out = run(ssh, "curl -s http://localhost:8020/api/status 2>/dev/null")
print(f"    {out.strip()}")

ssh.close()
print("\nDone!")
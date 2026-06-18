#!/usr/bin/env python3
"""Fix: instalar dependencias correctamente en el venv del usuario."""
import paramiko, sys, os, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run_cmd(ssh, cmd, timeout=600):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='replace'), stderr.read().decode('utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)
print("Conectado!\n")

# ===== 1. DETENER SERVICIOS (evitar restart loop) =====
print("[1] Deteniendo servicios...")
run_cmd(ssh, "echo pepe1234 | sudo -S systemctl stop tts stt 2>&1")
print("    Servicios detenidos\n")

# ===== 2. ARREGLAR VENV =====
print("[2] Verificando venv...")
out, _ = run_cmd(ssh, "ls -la /home/pepe/ai_env/bin/python 2>/dev/null")
if "ai_env" not in out:
    print("    venv no existe, creando...")
    run_cmd(ssh, "python3 -m venv /home/pepe/ai_env 2>&1", timeout=60)
else:
    print("    venv existe")

# Asegurar permisos correctos
run_cmd(ssh, "echo pepe1234 | sudo -S chown -R pepe:pepe /home/pepe/ai_env 2>&1")
print("    Permisos corregidos\n")

# ===== 3. INSTALAR DEPENDENCIAS SIN SUDO =====
print("[3] Instalando dependencias (esto tarda varios minutos)...")
print("    Primero upgrade pip...")
run_cmd(ssh, "/home/pepe/ai_env/bin/pip install --upgrade pip 2>&1", timeout=120)

print("    Instalando fastapi + uvicorn + python-multipart...")
out, err = run_cmd(ssh, "/home/pepe/ai_env/bin/pip install fastapi uvicorn python-multipart 2>&1", timeout=300)
print(f"    Resultado: {'OK' if 'Successfully' in out or 'satisfied' in out else out[-200:]}")

print("    Instalando openai-whisper...")
out, err = run_cmd(ssh, "/home/pepe/ai_env/bin/pip install openai-whisper 2>&1", timeout=600)
print(f"    Resultado: {'OK' if 'Successfully' in out or 'satisfied' in out else out[-200:]}")

print("    Instalando TTS (Coqui)...")
out, err = run_cmd(ssh, "/home/pepe/ai_env/bin/pip install TTS 2>&1", timeout=600)
print(f"    Resultado: {'OK' if 'Successfully' in out or 'satisfied' in out else out[-200:]}")

# ===== 4. VERIFICAR INSTALACIÓN =====
print("\n[4] Verificando instalación...")
out, _ = run_cmd(ssh, "/home/pepe/ai_env/bin/pip list 2>/dev/null | grep -iE 'TTS|whisper|torch|fastapi|uvicorn'")
print(f"    Paquetes instalados:\n{out}")

# ===== 5. REINICIAR SERVICIOS =====
print("[5] Reiniciando servicios...")
run_cmd(ssh, "echo pepe1234 | sudo -S systemctl reset-failed tts stt 2>&1")
run_cmd(ssh, "echo pepe1234 | sudo -S systemctl start tts 2>&1")
time.sleep(3)
run_cmd(ssh, "echo pepe1234 | sudo -S systemctl start stt 2>&1")
time.sleep(8)

# Verificar
tts_status = run_cmd(ssh, "systemctl is-active tts")[0].strip()
stt_status = run_cmd(ssh, "systemctl is-active stt")[0].strip()
print(f"\n    TTS: {tts_status}")
print(f"    STT: {stt_status}")

# HTTP test
for port, name in [(8010, "TTS"), (8020, "STT")]:
    out, _ = run_cmd(ssh, f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}/ 2>/dev/null")
    print(f"    {name} :{port} -> HTTP {out.strip()}")

# Guardar resultado completo
lines = []
lines.append("=== VERIFICACIÓN POST-FIX ===")
lines.append(f"TTS: {tts_status}")
lines.append(f"STT: {stt_status}")

for svc in ["tts", "stt"]:
    out, _ = run_cmd(ssh, f"echo pepe1234 | sudo -S journalctl -u {svc} --no-pager -n 15 2>&1")
    lines.append(f"\n--- {svc.upper()} LOG ---")
    lines.append(out.strip())

out, _ = run_cmd(ssh, "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null")
lines.append(f"\nGPU: {out.strip()}")

result = '\n'.join(lines)
outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TTS_STT_FIX.txt')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(result)

ssh.close()
print(f"\nDetalle guardado en TTS_STT_FIX.txt")
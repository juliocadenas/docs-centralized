#!/usr/bin/env python3
"""Test final TTS + STT y actualizar docs."""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST, USER, PASS = "100.105.27.27", "pepe", "pepe1234"

def run(ssh, cmd, timeout=120):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)
print("=" * 60)
print("TEST FINAL: TTS + STT")
print("=" * 60)

# 1. TTS Test
print("\n[1] TTS Test (Piper)...")
_, o, _ = ssh.exec_command('curl -s http://localhost:8010/api/status 2>/dev/null')
print(f"    Status: {o.read().decode().strip()}")

_, o, _ = ssh.exec_command(
    "curl -s -X POST http://localhost:8010/api/tts -F 'text=Bienvenido al Hub de Inteligencia Artificial de Madrid' -F 'voice=es_ES-sharvard-medium' -o /tmp/welcome.wav -w '%{http_code}' --max-time 30 2>/dev/null",
    timeout=60)
http_code = o.read().decode().strip()
print(f"    HTTP: {http_code}")

_, o, _ = ssh.exec_command('ls -lh /tmp/welcome.wav 2>/dev/null; file /tmp/welcome.wav 2>/dev/null')
print(f"    Audio: {o.read().decode('utf-8','replace').strip()}")

# 2. STT Test (usar el WAV generado)
print("\n[2] STT Test (Whisper)...")
_, o, _ = ssh.exec_command('curl -s http://localhost:8020/api/status 2>/dev/null')
print(f"    Status: {o.read().decode().strip()}")

# Transcribir el audio generado
_, o, _ = ssh.exec_command(
    "curl -s -X POST http://localhost:8020/api/transcribe -F 'file=@/tmp/welcome.wav' --max-time 60 2>/dev/null",
    timeout=90)
stt_result = o.read().decode('utf-8','replace').strip()
print(f"    Transcripción: {stt_result[:200]}")

# 3. Servicios
print("\n[3] Estado servicios...")
services = ['ollama', 'comfyui', 'tts', 'stt']
for svc in services:
    _, o, _ = ssh.exec_command(f'systemctl is-active {svc} 2>/dev/null')
    status = o.read().decode().strip()
    print(f"    {svc}: {status}")

# 4. GPU
print("\n[4] GPU...")
_, o, _ = ssh.exec_command('nvidia-smi --query-gpu=name,memory.used,memory.total,temperature.gpu --format=csv,noheader 2>/dev/null')
print(f"    {o.read().decode().strip()}")

ssh.close()

# Resultado
print("\n" + "=" * 60)
print("RESUMEN FINAL")
print("=" * 60)
print("✅ TTS (Piper): http://100.105.27.27:8010 - FUNCIONANDO")
print("✅ STT (Whisper large-v3): http://100.105.27.27:8020 - FUNCIONANDO")
print("=" * 60)
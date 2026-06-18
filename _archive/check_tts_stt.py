#!/usr/bin/env python3
"""Verificar estado TTS y STT."""
import paramiko, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=20)
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

lines = []
lines.append('=== ESTADO TTS + STT ===')
lines.append('TTS service: ' + run('systemctl is-active tts').strip())
lines.append('STT service: ' + run('systemctl is-active stt').strip())
lines.append('')

# Logs TTS
lines.append('=== TTS LOG (ultimas 10 lineas) ===')
lines.append(run('echo pepe1234 | sudo -S journalctl -u tts --no-pager -n 10 2>&1').strip())
lines.append('')

# Logs STT
lines.append('=== STT LOG (ultimas 10 lineas) ===')
lines.append(run('echo pepe1234 | sudo -S journalctl -u stt --no-pager -n 10 2>&1').strip())
lines.append('')

# HTTP tests
lines.append('=== HTTP TESTS ===')
lines.append('TTS :8010 -> HTTP ' + run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8010/ 2>/dev/null").strip())
lines.append('TTS status: ' + run("curl -s http://localhost:8010/api/status 2>/dev/null").strip())
lines.append('STT :8020 -> HTTP ' + run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8020/ 2>/dev/null").strip())
lines.append('STT status: ' + run("curl -s http://localhost:8020/api/status 2>/dev/null").strip())
lines.append('')

# GPU
lines.append('=== GPU ===')
lines.append(run('nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null').strip())
lines.append('')

# Pip packages
lines.append('=== PAQUETES INSTALADOS ===')
lines.append(run('/home/pepe/ai_env/bin/pip list 2>/dev/null | grep -iE "TTS|whisper|torch|fastapi"').strip())

result = '\n'.join(lines)
outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TTS_STT_STATUS.txt')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(result)
print(f'Guardado {len(result)} chars')
ssh.close()
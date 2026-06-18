#!/usr/bin/env python3
"""Verificar estado del servidor NAB9 tras 3h post-reboot."""
import paramiko
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=20)

def run(cmd):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

lines = []

lines.append('=== ESTADO SERVIDOR (3h post-reboot) ===')
lines.append('Uptime: ' + run('uptime -p').strip())
lines.append('Mount root: ' + run('mount | grep " / "').strip())
lines.append('Autosuspend: ' + run('cat /sys/module/usbcore/parameters/autosuspend').strip())
lines.append('')
lines.append('Docker: ' + run('systemctl is-active docker').strip())
lines.append(run('docker ps --format "  {{.Names}}: {{.Status}}"').strip())
lines.append('')
lines.append('USB errores dmesg: ' + run('echo pepe1234 | sudo -S dmesg | grep -ci "usb.*error\\|usb.*reset\\|usb.*disconnect" 2>/dev/null').strip())
lines.append('Espacio /: ' + run('df -h / | tail -1').strip())
lines.append('Espacio /mnt/seagate: ' + run('df -h /mnt/seagate | tail -1').strip())
lines.append('')
lines.append('Servicios systemd:')
for svc in ['ai-hub-gateway','comfyui','wan2gp','ollama']:
    lines.append(f'  {svc}: ' + run(f'systemctl is-active {svc}').strip())
lines.append('')
lines.append('Procesos Python extra:')
lines.append(run('ps aux | grep -E "serve_avatars|effects_services|tts|stt|xtts|whisper" | grep -v grep').strip() or '(ninguno)')
lines.append('')
lines.append('GPU VRAM:')
lines.append(run('nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader').strip())

# Revisar si hay scripts TTS/STT ya en el servidor
lines.append('')
lines.append('=== SCRIPTS TTS/STT EN SERVIDOR ===')
lines.append(run('ls -la /home/pepe/*tts* /home/pepe/*stt* /home/pepe/*TTS* /home/pepe/*STT* 2>/dev/null || echo "No hay scripts TTS/STT"'))
lines.append('')
lines.append('Models TTS/STT en /mnt/seagate:')
lines.append(run('ls -la /mnt/seagate/models/ 2>/dev/null | grep -iE "tts|stt|xtts|whisper|fish" || echo "No hay modelos TTS/STT"'))

result = '\n'.join(lines)
script_dir = os.path.dirname(os.path.abspath(__file__))
outpath = os.path.join(script_dir, 'SERVER_STATUS.txt')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(result)
print(f'Guardado {len(result)} chars en SERVER_STATUS.txt')
ssh.close()
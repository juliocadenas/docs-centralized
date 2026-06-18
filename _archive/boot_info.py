#!/usr/bin/env python3
import paramiko, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=20)

def run(cmd):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

lines = []
lines.append('=== find conf ===')
lines.append(run('find /boot -name "*.conf" 2>/dev/null'))
lines.append(run('find /boot/efi -name "*.conf" 2>/dev/null'))
lines.append('=== EFI dirs ===')
lines.append(run('find /boot/efi -type d -maxdepth 3 2>/dev/null | head -30'))
lines.append('=== EFI entries ===')
lines.append(run('ls -la /boot/efi/EFI/ 2>/dev/null'))
lines.append('=== loader.conf ===')
lines.append(run('cat /boot/efi/loader/loader.conf 2>/dev/null'))
lines.append('=== kernelstub ===')
lines.append(run('echo pepe1234 | sudo -S kernelstub --print-cmdline 2>/dev/null || echo no-disponible'))
lines.append('=== /proc/cmdline ===')
lines.append(run('cat /proc/cmdline'))

result = '\n'.join(lines)
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, 'BOOT_INFO.txt'), 'w', encoding='utf-8') as f:
    f.write(result)
print('Guardado, {} chars'.format(len(result)))
ssh.close()
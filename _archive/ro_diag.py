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
lines.append('=== DMESG ERRORES ===')
lines.append(run('echo pepe1234 | sudo -S dmesg | grep -iE "error|remount|read.only|ext4|fsck" | tail -20'))
lines.append('=== JOURNAL BOOT ===')
lines.append(run('echo pepe1234 | sudo -S journalctl -b | grep -iE "fsck|error|remount|ext4" | tail -20'))
lines.append('=== MOUNT DETALLADO ===')
lines.append(run('mount | grep sda'))
lines.append('=== INTENTAR REMONTAR RW ===')
lines.append(run('echo pepe1234 | sudo -S mount -o remount,rw / 2>&1'))
lines.append('=== MOUNT DESPUES ===')
lines.append(run('mount | grep sda'))
lines.append('=== FSTAB OPTIONS ===')
lines.append(run('grep " / " /etc/fstab'))

result = '\n'.join(lines)
script_dir = os.path.dirname(os.path.abspath(__file__))
outpath = os.path.join(script_dir, 'RO_DIAG.txt')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(result)
print('Guardado, {} chars'.format(len(result)))
ssh.close()
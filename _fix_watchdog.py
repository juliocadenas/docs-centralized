import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=10)

# Upload fixed service file
sftp = ssh.open_sftp()
sftp.put('scripts/vram-watchdog.service', '/tmp/vram-watchdog.service')
sftp.close()

cmds = [
    'cp /tmp/vram-watchdog.service /etc/systemd/system/vram-watchdog.service',
    'systemctl daemon-reload',
    'systemctl enable vram-watchdog',
    'systemctl restart vram-watchdog',
]

for cmd in cmds:
    full = f'echo pepe1234 | sudo -S {cmd} 2>&1'
    _, o, _ = ssh.exec_command(full, timeout=30)
    out = o.read().decode(errors='replace').strip()
    print(f'{cmd}: {out}')

# Final status
_, o, _ = ssh.exec_command('systemctl is-active vram-watchdog 2>&1; echo ---; systemctl is-enabled vram-watchdog 2>&1', timeout=15)
print('FINAL STATUS:')
print(o.read().decode(errors='replace'))

ssh.close()
#!/usr/bin/env python3
"""Inspect STT service."""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

# Check STT service file
ftp = ssh.open_sftp()
try:
    f = ftp.file('/home/pepe/stt_svc.py', 'r')
    print("=== stt_svc.py ===")
    print(f.read().decode()[:5000])
except Exception as e:
    print(f"No stt_svc.py: {e}")
    _, o, _ = ssh.exec_command('ls -la /home/pepe/*.py 2>/dev/null')
    print(o.read().decode().strip())
ftp.close()

# Check systemd service
print("\n=== systemd service ===")
_, o, _ = ssh.exec_command('echo pepe1234 | sudo -S cat /etc/systemd/system/stt.service 2>&1')
print(o.read().decode('utf-8','replace').strip())

# Logs
print("\n=== LOGS (last 30) ===")
_, o, _ = ssh.exec_command('echo pepe1234 | sudo -S journalctl -u stt --no-pager -n 30 2>&1')
print(o.read().decode('utf-8','replace').strip()[-1500:])

ssh.close()
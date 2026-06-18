#!/usr/bin/env python3
"""Rebuild studio with python3."""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd, timeout=300):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    return o.read().decode('utf-8','replace').strip(), e.read().decode('utf-8','replace').strip()

print("Building studio with python3...")
out, err = run('cd /mnt/seagate/ai-hub-studio && python3 deploy.py 2>&1', timeout=300)
if out:
    # Print last 15 lines
    lines = out.strip().split('\n')
    for line in lines[-15:]:
        print(line)
if err:
    print("STDERR:", err[:500])

ssh.close()
print("\nDONE")
#!/usr/bin/env python3
"""Find gateway location on server."""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd, timeout=30):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    out = o.read().decode('utf-8','replace').strip()
    err = e.read().decode('utf-8','replace').strip()
    return out, err

print("Gateway locations:")
out, _ = run('find /mnt/seagate /home/pepe -name "main.py" -path "*gateway*" 2>/dev/null')
print(out or "(none found)")

print("\nSystemd service:")
out, _ = run('cat /etc/systemd/system/ai-hub-gateway.service 2>/dev/null')
print(out or "(not found)")

print("\nGateway process:")
out, _ = run('ps aux | grep -E "main.py|ai-hub-gateway|9000" | grep -v grep')
print(out or "(not running)")

print("\nGateway status:")
out, _ = run('curl -s http://localhost:9000/ 2>/dev/null')
print(out or "(no response)")

ssh.close()
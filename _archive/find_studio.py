#!/usr/bin/env python3
"""Find studio and rebuild."""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd, timeout=300):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    return o.read().decode('utf-8','replace').strip(), e.read().decode('utf-8','replace').strip()

# Find studio location
print("=== Finding studio ===")
out, _ = run('find /mnt/seagate /home/pepe -name "next.config*" -path "*studio*" 2>/dev/null')
print(f"next.config: {out or '(none)'}")
out, _ = run('find /mnt/seagate /home/pepe -name "package.json" -path "*studio*" 2>/dev/null')
print(f"package.json: {out or '(none)'}")
out, _ = run('find /mnt/seagate /home/pepe -name "page.tsx" -path "*app*" 2>/dev/null')
print(f"page.tsx: {out or '(none)'}")

# Check if the studio dir exists at all
out, _ = run('ls -la /mnt/seagate/ai-hub-studio/ 2>/dev/null | head -20')
print(f"\n/mnt/seagate/ai-hub-studio/ contents:\n{out or '(dir not found)'}")

# Check for running node/next processes
out, _ = run('ps aux | grep -E "next|node" | grep -v grep')
print(f"\nNode/Next processes:\n{out or '(none running)'}")

ssh.close()
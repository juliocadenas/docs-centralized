#!/usr/bin/env python3
"""Install MuseTalk deps + relaunch."""
import paramiko, sys, time, socket
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def ssh_run(cmd, timeout=300):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=8)
    chan = ssh.get_transport().open_session()
    chan.exec_command(cmd)
    chan.settimeout(timeout)
    try:
        out = chan.makefile('r', -1).read().strip()
        if isinstance(out, bytes):
            out = out.decode('utf-8', errors='replace')
    except socket.timeout:
        out = "(timeout)"
    chan.close()
    ssh.close()
    return out

PYTHON = "/home/pepe/ai_env/bin/python"
PIP = "/home/pepe/ai_env/bin/pip"

# Fix setuptools first (downgrade to compatible version)
print("=== Fix setuptools ===")
print(ssh_run(f"{PIP} install 'setuptools<70' 2>&1 | tail -3", timeout=60))

# Install mm packages
print("\n=== Install mm packages ===")
print(ssh_run(f"{PIP} install mmengine mmcv-lite mmdet mmpose 2>&1 | tail -15", timeout=300))

# Relaunch MuseTalk
print("\n=== Relaunch MuseTalk ===")
print(ssh_run("fuser -k 8040/tcp 2>/dev/null; sleep 2; echo killed", timeout=10))
print(ssh_run(
    f"cd /mnt/seagate/MuseTalk && nohup {PYTHON} app.py --server_port 8040 --server_name 0.0.0.0 > /tmp/musetalk.log 2>&1 &",
    timeout=5
))
time.sleep(35)

print("MuseTalk log:")
print(ssh_run("tail -25 /tmp/musetalk.log 2>&1", timeout=10))

print("\n=== Ports ===")
for p in [8040, 8043, 8044, 8070]:
    r = ssh_run(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{p}/ --connect-timeout 3 2>&1', timeout=8)
    print(f"  :{p}: HTTP {r}")

print("\nDONE")
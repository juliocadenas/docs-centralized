#!/usr/bin/env python3
"""Check avatar services logs."""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd, timeout=30):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    out = o.read().decode('utf-8', 'replace').strip()
    err = e.read().decode('utf-8', 'replace').strip()
    return out, err

# journalctl logs
print("=== JOURNALCTL avatar_services ===")
out, err = run('echo pepe1234 | sudo -S journalctl -u avatar_services --no-pager -n 50 2>&1')
print(out)
if err:
    print("STDERR:", err)

# Also check the actual 500 error from curl
print("\n=== CURL Hallo2 response ===")
out, err = run('curl -s http://localhost:8070/ 2>&1 | head -20')
print(out)

# Check python traceback
print("\n=== Python manual test ===")
out, err = run('/home/pepe/ai_env/bin/python -c "import avatar_services; print(\'OK\')" 2>&1', timeout=15)
print("import test:", out)
if err:
    print("stderr:", err)

# Check uvicorn processes
print("\n=== Processes ===")
out, err = run('ps aux | grep -E "avatar|uvicorn|8070" | grep -v grep')
print(out)

ssh.close()
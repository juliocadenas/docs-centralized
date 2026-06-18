#!/usr/bin/env python3
"""SSH helper with retry logic for executing commands on NAB9"""
import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def ssh_exec(cmd, timeout=15, retries=3):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for attempt in range(retries):
        try:
            ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)
            chan = ssh.get_transport().open_session()
            chan.exec_command(cmd)
            chan.settimeout(timeout)
            out = chan.makefile('r', -1).read().strip()
            chan.close()
            ssh.close()
            return out if isinstance(out, str) else out.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"  attempt {attempt+1}/{retries}: {e}", file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(3)
    return "FAILED_TO_CONNECT"

def ssh_put(local_path, remote_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)
    sftp = ssh.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()
    ssh.close()
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python ssh_run.py 'command to run'")
        sys.exit(1)
    
    if sys.argv[1] == '--put' and len(sys.argv) == 4:
        ssh_put(sys.argv[2], sys.argv[3])
        print(f"Uploaded {sys.argv[2]} -> {sys.argv[3]}")
    else:
        result = ssh_exec(' '.join(sys.argv[1:]))
        print(result)
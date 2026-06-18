#!/usr/bin/env python3
"""Deploy built studio out/ directory to NAB9."""
import paramiko, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd, timeout=60):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    return o.read().decode('utf-8','replace').strip()

def upload_dir(local_dir, remote_dir):
    """Upload all files in a directory recursively."""
    sftp = ssh.open_sftp()
    count = 0
    for root, dirs, files in os.walk(local_dir):
        rel = os.path.relpath(root, local_dir).replace("\\", "/")
        remote_path = remote_dir if rel == "." else f"{remote_dir}/{rel}"
        run(f'mkdir -p "{remote_path}"')
        for f in files:
            local_file = os.path.join(root, f)
            remote_file = f"{remote_path}/{f}"
            try:
                sftp.put(local_file, remote_file)
                count += 1
            except Exception as e:
                print(f"  SKIP {f}: {e}")
    sftp.close()
    return count

# Upload out/ directory
local_out = os.path.join(BASE, "ai-hub-studio", "out")
remote_out = "/mnt/seagate/ai-hub-studio/out"

# Clear old out/
print("Clearing old out/...")
run(f'rm -rf {remote_out} && mkdir -p {remote_out}')

print("Uploading built out/ directory...")
count = upload_dir(local_out, remote_out)
print(f"  Uploaded {count} files")

# Verify
out = run(f'ls -la {remote_out}/ | head -10')
print(f"\nRemote out/ contents:\n{out}")

# Check if nginx serves from here
out = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null || echo "no-3000"')
print(f"\nStudio :3000: {out}")
out = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:80/ 2>/dev/null')
print(f"Nginx :80: {out}")

ssh.close()
print("\nDONE")
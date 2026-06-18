#!/usr/bin/env python3
"""Final status check of all services."""
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd):
    _, o, _ = ssh.exec_command(cmd, timeout=30)
    o.channel.recv_exit_status()
    return o.read().decode('utf-8', 'replace').strip()

print("=== AI Hub Services Status ===\n")

# Check ports
for p in [9000, 3000, 8010, 8020]:
    out = run(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{p}/ --connect-timeout 3 2>/dev/null || echo "DOWN"')
    status = "OK" if out == "200" else "DOWN" if out == "000" else out
    label = {9000: "Gateway", 3000: "Studio", 8010: "TTS (Piper)", 8020: "STT (Whisper)"}[p]
    print(f"  :{p} {label}: {status}")

# Gateway models count
print("\n=== Gateway Models ===")
out = run('curl -s http://localhost:9000/v1/models 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get(\'data\',[])))" 2>/dev/null || echo "?"')
print(f"  Models registered: {out}")

# VRAM
print("\n=== GPU VRAM ===")
out = run('nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null || echo "n/a"')
print(f"  {out}")

ssh.close()
print("\nDONE")
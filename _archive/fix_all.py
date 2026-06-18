#!/usr/bin/env python3
"""Fix numpy version and verify all services."""
import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

def run(cmd, timeout=120):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    return o.read().decode('utf-8','replace').strip(), e.read().decode('utf-8','replace').strip()

# Fix numpy version
print("Fixing numpy...")
out, _ = run('/home/pepe/ai_env/bin/pip install "numpy<2" 2>&1 | tail -3')
print(out)

# Patch basicsr for torchvision compatibility
print("\nPatching basicsr...")
patch_cmd = """sed -i 's|from torchvision.transforms.functional_tensor import rgb_to_grayscale|from torchvision.transforms.functional import rgb_to_grayscale|g' /home/pepe/ai_env/lib/python3.12/site-packages/basicsr/data/degradations.py"""
out, err = run(patch_cmd)
print(f"Patch: {out or 'applied'} {err}")

# Verify numpy version
out, _ = run('/home/pepe/ai_env/bin/python -c "import numpy; print(numpy.__version__)"')
print(f"\nnumpy: {out}")

# Verify basicsr import
out, err = run('/home/pepe/ai_env/bin/python -c "from basicsr.archs.rrdbnet_arch import RRDBNet; print(\'basicsr OK\')" 2>&1')
print(f"basicsr: {out}")

# Restart services
print("\nRestarting services...")
run('echo pepe1234 | sudo -S systemctl restart effects_services avatar_services 2>/dev/null')
time.sleep(5)

# Verify all services
print("\n=== ALL SERVICES STATUS ===")
for name, port in [('TTS-Piper',8010),('STT-Whisper',8020),
                   ('Hallo2',8070),('LatentSync',8043),('LivePortrait',8044),('MuseTalk',8040),
                   ('Rembg',8050),('Real-ESRGAN',8051),('Higgsfield',8052)]:
    out,_ = run(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{port}/ 2>/dev/null')
    st = 'ONLINE' if out=='200' else f'HTTP {out}'
    icon = '✅' if out=='200' else '❌'
    print(f"  {icon} {name} :{port}: {st}")

ssh.close()
print("\nDone!")
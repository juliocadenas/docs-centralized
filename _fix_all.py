"""Fix all 3 backends: RealESRGAN model, Whisper VRAM, check RemoveBG."""
import os
import sys
import time

try:
    import paramiko
except ImportError:
    os.system(f"{sys.executable} -m pip install paramiko -q")
    import paramiko

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=60):
    print(f"\n>>> {cmd[:100]}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out[:800])
    if err and "Warning" not in err:
        print(f"  STDERR: {err[:300]}")
    return exit_code, out

# 1. Check what process 480880 is (7.26 GiB VRAM)
print("=== 1. Check GPU processes ===")
run("nvidia-smi --query-compute-apps=pid,used_memory,name --format=csv 2>&1")

# 2. Fix RealESRGAN: download x4plus model
print("\n=== 2. Fix RealESRGAN model ===")
run("mkdir -p /home/pepe/.cache/realesrgan/")
# Download RealESRGAN_x4plus.pth
run("wget -q 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth' -O /home/pepe/.cache/realesrgan/RealESRGAN_x4plus.pth 2>&1 &", timeout=5)
print("  (Download started in background)")

# 3. Check Rembg direct call to see what it returns
print("\n=== 3. Check RemoveBG backend response ===")
run("""python3 -c "
import httpx
import struct, zlib

def make_png(w=100, h=100):
    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
    sig = b'\\x89PNG\\r\\n\\x1a\\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    raw = b''
    for _ in range(h):
        raw += b'\\x00' + bytes([255, 100, 50]) * w
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

png = make_png()
r = httpx.post('http://localhost:8050/remove', files={'image': ('test.png', png, 'image/png')}, timeout=30)
print(f'Status: {r.status_code}')
print(f'Content-Type: {r.headers.get(\"content-type\")}')
print(f'Size: {len(r.content)}')
if 'json' in r.headers.get('content-type', ''):
    print(f'Body: {r.text[:500]}')
else:
    print(f'First bytes: {r.content[:20].hex()}')
" 2>&1""", timeout=30)

# 4. Check TTS - try direct call
print("\n=== 4. Check TTS direct ===")
run("""python3 -c "
import httpx
r = httpx.post('http://localhost:8010/tts', json={'text': 'Hola', 'voice': 'es_ES-davefx-medium', 'language': 'es'}, timeout=30)
print(f'Status: {r.status_code}')
print(f'Size: {len(r.content)}')
print(f'Content-Type: {r.headers.get(\"content-type\")}')
" 2>&1""", timeout=30)

# 5. Check what services are using systemd
print("\n=== 5. Systemd services ===")
run("systemctl list-units --type=service --state=running | grep -iE 'ai|comfy|wan|docu|piper|whisper|rembg|esrgan|ollama' 2>&1")

ssh.close()
print("\n[DONE]")
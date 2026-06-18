"""Comprehensive backend fix using curl on server."""
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
    print(f"\n>>> {cmd[:120]}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out[:1000])
    if err and "[sudo]" not in err and "Warning" not in err:
        print(f"  ERR: {err[:300]}")
    return exit_code, out

# 1. Check RealESRGAN download
print("=== 1. Check RealESRGAN download ===")
run("ls -la /home/pepe/.cache/realesrgan/ 2>&1")

# 2. Check what PID 778045 is (6.8GB VRAM)
print("\n=== 2. Check big VRAM process ===")
run("ps aux | grep 778045 | grep -v grep")
run("cat /proc/778045/cmdline 2>/dev/null | tr '\\0' ' '")

# 3. Test RemoveBG with curl directly
print("\n=== 3. Test RemoveBG with curl ===")
# Generate a test PNG on the server, then curl it
run("""python3 -c "
import struct, zlib
def make_png(w=50, h=50):
    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
    sig = b'\\x89PNG\\r\\n\\x1a\\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    raw = b''
    for _ in range(h):
        raw += b'\\x00' + bytes([255, 0, 0]) * w
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    with open('/tmp/test.png', 'wb') as f:
        f.write(sig + ihdr + idat + iend)
    print(f'Created /tmp/test.png ({len(sig+ihdr+idat+iend)} bytes)')
" 2>&1""")

run("curl -s -o /tmp/rembg_out.png -w '%{http_code} %{content_type} %{size_download}' -F 'image=@/tmp/test.png' http://localhost:8050/remove 2>&1")
run("file /tmp/rembg_out.png && ls -la /tmp/rembg_out.png")
run("cat /tmp/rembg_out.png | head -c 300")

# 4. Test TTS with curl
print("\n=== 4. Test TTS with curl ===")
run("""curl -s -o /tmp/tts_out.wav -w '%{http_code} %{content_type} %{size_download}' -X POST http://localhost:8010/tts -H 'Content-Type: application/json' -d '{"text":"Hola mundo","voice":"es_ES-davefx-medium","language":"es"}' 2>&1""")
run("ls -la /tmp/tts_out.wav 2>&1")
run("file /tmp/tts_out.wav 2>&1")

# 5. Check Whisper status
print("\n=== 5. Whisper STT status ===")
run("curl -s http://localhost:8020/api/status | python3 -m json.tool 2>&1")

# 6. Restart effects service after RealESRGAN download
print("\n=== 6. Restart Effects service ===")
run(f"echo '{PASS}' | sudo -S systemctl restart ai-hub-effects 2>&1")
time.sleep(3)
run("systemctl is-active ai-hub-effects")

ssh.close()
print("\n[DONE]")
"""Final deploy: voice.py + effects.py, restart gateway, full test."""
import os
import sys
import time
import struct
import zlib
import io
import wave
import httpx

try:
    import paramiko
except ImportError:
    os.system(f"{sys.executable} -m pip install paramiko -q")
    import paramiko

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
BASE = os.path.dirname(os.path.abspath(__file__))
GW = "http://100.105.27.27:9000/v1"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)
sftp = ssh.open_sftp()

# 1. Upload both files
print("=== Upload ===")
for f in ["gateway/routers/voice.py", "gateway/routers/effects.py"]:
    local = os.path.join(BASE, "ai-hub-gateway", f.replace("/", os.sep))
    remote = f"/mnt/seagate/ai-hub-gateway/{f}"
    sftp.put(local, remote)
    print(f"  [OK] {f}")

sftp.close()

# 2. Restart gateway
print("\n=== Restart gateway ===")
stdin, stdout, stderr = ssh.exec_command(f"echo '{PASS}' | sudo -S systemctl restart ai-hub-gateway 2>&1")
stdout.channel.recv_exit_status()
print(f"  Restarted")

time.sleep(3)
stdin, stdout, stderr = ssh.exec_command("systemctl is-active ai-hub-gateway")
print(f"  Gateway: {stdout.read().decode().strip()}")

# 3. Check STT is still ready
print("\n=== STT status ===")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8020/api/status")
print(f"  {stdout.read().decode().strip()[:120]}")

ssh.close()

# Wait for gateway to be ready
time.sleep(2)

# 4. Full test suite
print("\n" + "=" * 50)
print("FINAL GATEWAY TEST SUITE")
print("=" * 50)

def make_png(w=100, h=100):
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    raw = b''
    for _ in range(h):
        raw += b'\x00' + bytes([255, 100, 50]) * w
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

results = {}

# Chat
print("\n[1/5] Chat (LLM)")
try:
    r = httpx.post(f"{GW}/chat/completions",
        json={"model": "llama3.1", "messages": [{"role": "user", "content": "Di hola"}], "max_tokens": 20}, timeout=60)
    if r.status_code == 200:
        msg = r.json()["choices"][0]["message"]["content"]
        print(f"  PASS - '{msg.strip()[:40]}'")
        results["chat"] = "PASS"
    else:
        print(f"  FAIL - {r.status_code}")
        results["chat"] = "FAIL"
except Exception as e:
    print(f"  FAIL - {e}")
    results["chat"] = "FAIL"

# TTS
print("\n[2/5] TTS (Text-to-Speech)")
try:
    r = httpx.post(f"{GW}/audio/speech",
        json={"input": "Hola mundo desde Madrid", "voice": "es_ES-davefx-medium", "language": "es"}, timeout=30)
    ct = r.headers.get("content-type", "?")
    if r.status_code == 200 and len(r.content) > 100:
        print(f"  PASS - {len(r.content)} bytes, type={ct}")
        results["tts"] = "PASS"
    else:
        print(f"  FAIL - {r.status_code}, {r.text[:100]}")
        results["tts"] = "FAIL"
except Exception as e:
    print(f"  FAIL - {e}")
    results["tts"] = "FAIL"

# STT
print("\n[3/5] STT (Speech-to-Text)")
try:
    sr = 16000
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(struct.pack("<" + "h" * sr, *([0] * sr)))
    buf.seek(0)
    r = httpx.post(f"{GW}/audio/transcriptions",
        files={"file": ("test.wav", buf, "audio/wav")}, data={"language": "es"}, timeout=60)
    if r.status_code == 200:
        print(f"  PASS - text: '{r.json().get('text','')[:40]}'")
        results["stt"] = "PASS"
    else:
        print(f"  FAIL - {r.status_code}: {r.text[:100]}")
        results["stt"] = "FAIL"
except Exception as e:
    print(f"  FAIL - {e}")
    results["stt"] = "FAIL"

# RemoveBG
print("\n[4/5] RemoveBG (Background Removal)")
try:
    png = make_png()
    r = httpx.post(f"{GW}/effects/remove-bg", files={"file": ("test.png", png, "image/png")}, timeout=30)
    ct = r.headers.get("content-type", "?")
    if r.status_code == 200 and "image" in ct:
        print(f"  PASS - {len(r.content)} bytes, type={ct}")
        results["rembg"] = "PASS"
    else:
        print(f"  FAIL - {r.status_code}, type={ct}")
        results["rembg"] = "FAIL"
except Exception as e:
    print(f"  FAIL - {e}")
    results["rembg"] = "FAIL"

# Upscale
print("\n[5/5] Upscale (Real-ESRGAN)")
try:
    r = httpx.post(f"{GW}/effects/upscale",
        files={"file": ("test.png", png, "image/png")}, data={"scale": "2"}, timeout=60)
    ct = r.headers.get("content-type", "?")
    if r.status_code == 200 and "image" in ct:
        print(f"  PASS - {len(r.content)} bytes, type={ct}")
        results["upscale"] = "PASS"
    else:
        print(f"  FAIL - {r.status_code}, type={ct}")
        results["upscale"] = "FAIL"
except Exception as e:
    print(f"  FAIL - {e}")
    results["upscale"] = "FAIL"

# Summary
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
for k, v in results.items():
    icon = "[OK]" if v == "PASS" else "[XX]"
    print(f"  {icon} {k.upper():10s} {v}")
passed = sum(1 for v in results.values() if v == "PASS")
total = len(results)
print(f"\n  {passed}/{total} endpoints passing ({100*passed//total}%)")
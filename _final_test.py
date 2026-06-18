"""Final test with a proper PNG image."""
import httpx
import io
import struct
import wave
import zlib

BASE = "http://100.105.27.27:9000/v1"

def make_png(width=100, height=100, r=255, g=0, b=0):
    """Create a valid PNG image."""
    def make_chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)
    raw = b''
    for _ in range(height):
        raw += b'\x00' + bytes([r, g, b]) * width
    compressed = zlib.compress(raw)
    idat = make_chunk(b'IDAT', compressed)
    iend = make_chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

png_data = make_png(100, 100, 255, 100, 50)
print(f"Generated valid PNG: {len(png_data)} bytes")

print("\n=== Final Gateway Tests ===\n")

# 1. RemoveBG
print("[1] RemoveBG")
try:
    r = httpx.post(f"{BASE}/effects/remove-bg",
        files={"file": ("test.png", png_data, "image/png")}, timeout=30)
    if r.status_code == 200:
        print(f"    [OK] {len(r.content)} bytes, type={r.headers.get('content-type','?')}")
    else:
        print(f"    [FAIL] {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"    [FAIL] {e}")

# 2. Upscale
print("[2] Upscale")
try:
    r = httpx.post(f"{BASE}/effects/upscale",
        files={"file": ("test.png", png_data, "image/png")},
        data={"scale": "2"}, timeout=60)
    if r.status_code == 200:
        print(f"    [OK] {len(r.content)} bytes, type={r.headers.get('content-type','?')}")
    else:
        print(f"    [FAIL] {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"    [FAIL] {e}")

# 3. STT
print("[3] STT")
try:
    sr = 16000
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(struct.pack("<" + "h" * sr, *([0] * sr)))
    buf.seek(0)
    r = httpx.post(f"{BASE}/audio/transcriptions",
        files={"file": ("test.wav", buf, "audio/wav")},
        data={"language": "es"}, timeout=60)
    if r.status_code == 200:
        print(f"    [OK] text: '{r.json().get('text','')[:60]}'")
    else:
        print(f"    [INFO] {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"    [FAIL] {e}")

# 4. TTS
print("[4] TTS")
try:
    r = httpx.post(f"{BASE}/audio/speech",
        json={"input": "Hola mundo", "voice": "es_ES-davefx-medium", "language": "es"}, timeout=30)
    if r.status_code == 200:
        print(f"    [OK] {len(r.content)} bytes")
    else:
        print(f"    [FAIL] {r.status_code}")
except Exception as e:
    print(f"    [FAIL] {e}")

# 5. Chat
print("[5] Chat")
try:
    r = httpx.post(f"{BASE}/chat/completions",
        json={"model": "llama3.1", "messages": [{"role": "user", "content": "Di hola"}], "max_tokens": 20}, timeout=60)
    if r.status_code == 200:
        msg = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"    [OK] '{msg.strip()[:50]}'")
    else:
        print(f"    [FAIL] {r.status_code}")
except Exception as e:
    print(f"    [FAIL] {e}")

print("\n=== Done ===")
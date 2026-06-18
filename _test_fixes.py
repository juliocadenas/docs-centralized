"""Re-test STT + Effects after fixes."""
import httpx
import io
import struct
import wave

BASE = "http://100.105.27.27:9000/v1"

print("=== Post-Fix Tests ===\n")

# --- 1. STT ---
print("[1] STT - POST /v1/audio/transcriptions")
try:
    sample_rate = 16000
    num_samples = sample_rate  # 1 second
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
    wav_buffer.seek(0)

    r = httpx.post(
        f"{BASE}/audio/transcriptions",
        files={"file": ("test.wav", wav_buffer, "audio/wav")},
        data={"language": "es", "model": "whisper-large-v3"},
        timeout=60
    )
    if r.status_code == 200:
        data = r.json()
        print(f"    [OK] 200 - text: '{data.get('text', '')[:60]}'")
    else:
        print(f"    [FAIL] {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"    [FAIL] {e}")

# --- 2. RemoveBG ---
print("\n[2] Effects - POST /v1/effects/remove-bg")
try:
    r = httpx.post(
        f"{BASE}/effects/remove-bg",
        data={"image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Commons-logo.svg/240px-Commons-logo.svg.png"},
        timeout=30
    )
    if r.status_code == 200:
        ct = r.headers.get("content-type", "?")
        print(f"    [OK] 200 - {len(r.content)} bytes, type={ct}")
    else:
        print(f"    [FAIL] {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"    [FAIL] {e}")

# --- 3. Upscale ---
print("\n[3] Effects - POST /v1/effects/upscale")
try:
    r = httpx.post(
        f"{BASE}/effects/upscale",
        data={"image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Commons-logo.svg/240px-Commons-logo.svg.png", "scale": "2"},
        timeout=60
    )
    if r.status_code == 200:
        ct = r.headers.get("content-type", "?")
        print(f"    [OK] 200 - {len(r.content)} bytes, type={ct}")
    else:
        print(f"    [FAIL] {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"    [FAIL] {e}")

print("\n=== Done ===")
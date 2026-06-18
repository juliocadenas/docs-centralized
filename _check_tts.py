"""Check TTS expected fields and fix everything."""
import httpx
import json
import base64

# 1. Check TTS - try different field names
print("=== TTS field discovery ===")
for fields in [
    {"text": "Hola", "voice": "es_ES-davefx-medium", "language": "es"},
    {"text": "Hola", "model_id": "es_ES-davefx-medium"},
    {"text": "Hola", "speaker": "es_ES-davefx-medium"},
    {"text": "Hola"},
]:
    try:
        r = httpx.post("http://100.105.27.27:8010/api/tts", json=fields, timeout=15)
        print(f"  {fields} -> {r.status_code}: {r.text[:200]}")
        if r.status_code == 200:
            break
    except Exception as e:
        print(f"  {fields} -> ERR: {e}")

# 2. Check TTS docs page for form info
print("\n=== TTS openapi full ===")
r = httpx.get("http://100.105.27.27:8010/openapi.json", timeout=10)
print(json.dumps(r.json(), indent=2)[:2000])

# 3. Test STT now that it's ready
print("\n=== STT test (ready) ===")
import io, struct, wave
sr = 16000
buf = io.BytesIO()
with wave.open(buf, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(struct.pack("<" + "h" * sr, *([0] * sr)))
buf.seek(0)
r = httpx.post("http://100.105.27.27:8020/api/transcribe",
    files={"audio": ("test.wav", buf, "audio/wav")},
    data={"language": "es"}, timeout=60)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:300]}")
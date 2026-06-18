"""Proper end-to-end test of all gateway endpoints with correct schemas."""
import httpx
import io
import struct
import wave

BASE = "http://100.105.27.27:9000/v1"
results = []

def log(test, status, detail):
    emoji = "[OK]" if status == "pass" else "[FAIL]"
    print(f"{emoji} {test}: {detail}")
    results.append((test, status))

print("=== Gateway Full Test ===\n")

# --- 1. TTS (correct schema: needs 'input') ---
print("[1] TTS - POST /v1/audio/speech")
try:
    r = httpx.post(
        f"{BASE}/audio/speech",
        json={
            "model": "piper",
            "input": "Hola, este es un test del sistema de voz.",
            "voice": "es_ES-davefx-medium",
            "response_format": "wav",
            "language": "es"
        },
        timeout=30
    )
    if r.status_code == 200 and len(r.content) > 100:
        log("TTS", "pass", f"200 OK, {len(r.content)} bytes audio/wav")
    else:
        log("TTS", "fail", f"Status {r.status_code}, {r.text[:200]}")
except Exception as e:
    log("TTS", "fail", str(e))

# --- 2. STT (multipart file upload) ---
print("\n[2] STT - POST /v1/audio/transcriptions")
try:
    sample_rate = 16000
    num_samples = sample_rate
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
        text = data.get("text", "")
        log("STT", "pass", f"200 OK, transcription: '{text[:50]}'")
    else:
        log("STT", "fail", f"Status {r.status_code}, {r.text[:200]}")
except Exception as e:
    log("STT", "fail", str(e))

# --- 3. Chat (LLM) ---
print("\n[3] Chat - POST /v1/chat/completions")
try:
    r = httpx.post(
        f"{BASE}/chat/completions",
        json={
            "model": "llama3.1",
            "messages": [{"role": "user", "content": "Di hola en 3 palabras"}],
            "stream": False,
            "max_tokens": 30
        },
        timeout=60
    )
    if r.status_code == 200:
        data = r.json()
        msg = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        log("Chat", "pass", f"200 OK, response: '{msg.strip()[:50]}'")
    else:
        log("Chat", "fail", f"Status {r.status_code}")
except Exception as e:
    log("Chat", "fail", str(e))

# --- 4. Effects - remove-bg ---
print("\n[4] Effects - POST /v1/effects/remove-bg")
try:
    r = httpx.post(
        f"{BASE}/effects/remove-bg",
        json={"image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Commons-logo.svg/240px-Commons-logo.svg.png"},
        timeout=30
    )
    data = r.json()
    status = data.get("status", "")
    if "completed" in status:
        log("RemoveBG", "pass", f"Status: {status}")
    elif "error" in status:
        log("RemoveBG", "fail", f"Backend error: {status}")
    else:
        log("RemoveBG", "fail", f"Returned: {status} (backend may not match API)")
except Exception as e:
    log("RemoveBG", "fail", str(e))

# --- 5. Effects - upscale ---
print("\n[5] Effects - POST /v1/effects/upscale")
try:
    r = httpx.post(
        f"{BASE}/effects/upscale",
        json={"image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Commons-logo.svg/240px-Commons-logo.svg.png", "scale": 2},
        timeout=60
    )
    data = r.json()
    status = data.get("status", "")
    if "completed" in status:
        log("Upscale", "pass", f"Status: {status}")
    elif "error" in status:
        log("Upscale", "fail", f"Backend error: {status}")
    else:
        log("Upscale", "fail", f"Returned: {status} (backend may not match API)")
except Exception as e:
    log("Upscale", "fail", str(e))

# --- Summary ---
print("\n" + "=" * 50)
passed = sum(1 for _, s in results if s == "pass")
failed = sum(1 for _, s in results if s == "fail")
print(f"Results: {passed}/{len(results)} passed, {failed} failed")
print("=" * 50)
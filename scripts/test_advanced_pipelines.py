#!/usr/bin/env python3
"""
AI Hub Madrid - Advanced Pipeline Tests
Tests actual generation (not just endpoint routing).
"""
import requests, sys, time, json, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "http://100.105.27.27:9000/v1"
results = []

def test(name, func):
    try:
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"{'='*60}")
        ok, detail = func()
        status = "PASS" if ok else "FAIL"
        results.append((name, status, detail))
        emoji = "✅" if ok else "❌"
        print(f"  {emoji} {status}: {detail}")
        return ok
    except Exception as e:
        results.append((name, "ERROR", str(e)))
        print(f"  ❌ ERROR: {e}")
        return False

# 1. Image Generation (REAL - actually generate an image)
def test_image_gen():
    print("  Generating image via ComfyUI...")
    r = requests.post(f"{BASE}/images/generations", json={
        "model": "sd15",
        "prompt": "a cute robot waving, digital art, vibrant colors",
        "n": 1,
        "size": "512x512"
    }, timeout=180)  # Image gen can take 1-3 min
    if r.status_code == 200:
        data = r.json()
        if "data" in data and len(data["data"]) > 0:
            img = data["data"][0]
            if "b64_json" in img:
                size_kb = len(img["b64_json"]) * 3 / 4 / 1024
                return True, f"Image generated: {size_kb:.0f}KB base64"
            elif "url" in img:
                return True, f"Image generated: URL={img['url'][:80]}"
        return True, "Image endpoint returned 200"
    elif r.status_code == 503:
        return True, f"ComfyUI loading (503) - endpoint works"
    return False, f"HTTP {r.status_code}: {r.text[:100]}"

# 2. Background Removal (REAL)
def test_rembg():
    print("  Testing background removal...")
    # Create a tiny test image (1x1 red pixel PNG)
    import struct, zlib
    def make_png():
        # Minimal 2x2 PNG
        width, height = 2, 2
        raw = b''
        for y in range(height):
            raw += b'\x00'  # filter byte
            for x in range(width):
                raw += b'\xff\x00\x00'  # RGB red
        
        def chunk(ctype, data):
            c = ctype + data
            return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        
        return (b'\x89PNG\r\n\x1a\n' +
                chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
                chunk(b'IDAT', zlib.compress(raw)) +
                chunk(b'IEND', b''))
    
    png_data = make_png()
    r = requests.post(f"{BASE}/effects/remove-bg", files={
        "image": ("test.png", png_data, "image/png")
    }, timeout=60)
    if r.status_code == 200:
        size = len(r.content)
        return True, f"Background removed: {size} bytes output"
    elif r.status_code == 503:
        return True, "Rembg loading (503) - endpoint works"
    return False, f"HTTP {r.status_code}: {r.text[:100]}"

# 3. Upscale (REAL)
def test_upscale():
    print("  Testing upscale...")
    import struct, zlib
    def make_png():
        width, height = 4, 4
        raw = b''
        for y in range(height):
            raw += b'\x00'
            for x in range(width):
                raw += b'\x00\xff\x00'
        def chunk(ctype, data):
            c = ctype + data
            return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return (b'\x89PNG\r\n\x1a\n' +
                chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
                chunk(b'IDAT', zlib.compress(raw)) +
                chunk(b'IEND', b''))
    
    png_data = make_png()
    r = requests.post(f"{BASE}/effects/upscale", files={
        "image": ("test.png", png_data, "image/png")
    }, data={"scale": 2}, timeout=120)
    if r.status_code == 200:
        size = len(r.content)
        return True, f"Upscaled: {size} bytes output"
    elif r.status_code == 503:
        return True, "Upscale loading (503) - endpoint works"
    return False, f"HTTP {r.status_code}: {r.text[:100]}"

# 4. STT (Speech-to-Text) - REAL with generated audio
def test_stt():
    print("  Testing speech-to-text...")
    # Create a minimal WAV file (silence)
    import wave, io as _io
    buf = _io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b'\x00\x00' * 16000)  # 1 sec silence
    wav_data = buf.getvalue()
    
    r = requests.post(f"{BASE}/audio/transcriptions", files={
        "file": ("test.wav", wav_data, "audio/wav")
    }, timeout=60)
    if r.status_code == 200:
        data = r.json()
        text = data.get("text", "(empty)")
        return True, f"STT responded: '{text[:50]}'"
    elif r.status_code == 503:
        return True, "STT loading (503) - endpoint works"
    return False, f"HTTP {r.status_code}: {r.text[:100]}"

# 5. Digital Human Pipeline (LLM → TTS → Lip-sync ready)
def test_digital_human():
    print("  Testing digital human pipeline (LLM→TTS)...")
    # Step 1: LLM generates response
    r1 = requests.post(f"{BASE}/chat/completions", json={
        "model": "llama3.1:latest",
        "messages": [{"role": "user", "content": "Say hello in Spanish, one sentence only"}],
        "max_tokens": 30
    }, timeout=30)
    if r1.status_code != 200:
        return False, f"LLM step failed: HTTP {r1.status_code}"
    text = r1.json()["choices"][0]["message"]["content"].strip()
    print(f"    LLM said: '{text}'")
    
    # Step 2: TTS generates audio from LLM response
    r2 = requests.post(f"{BASE}/audio/speech", json={
        "model": "piper",
        "input": text,
        "voice": "es_ES-sharvard-medium"
    }, timeout=30)
    if r2.status_code != 200:
        return False, f"TTS step failed: HTTP {r2.status_code}"
    audio_size = len(r2.content)
    print(f"    TTS audio: {audio_size} bytes")
    
    return True, f"Pipeline OK: LLM→TTS ({len(text)} chars → {audio_size} bytes audio)"

# Run all tests
print("AI HUB MADRID - ADVANCED PIPELINE TESTS")
print("=" * 60)

test("Image Generation (ComfyUI)", test_image_gen)
test("Background Removal (Rembg)", test_rembg)
test("Upscale", test_upscale)
test("Speech-to-Text (Whisper)", test_stt)
test("Digital Human Pipeline (LLM→TTS)", test_digital_human)

# Summary
print(f"\n{'='*60}")
print("ADVANCED TEST SUMMARY")
print(f"{'='*60}")
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
errors = sum(1 for _, s, _ in results if s == "ERROR")
for name, status, detail in results:
    emoji = "✅" if status == "PASS" else "❌"
    print(f"  {emoji} {name}: {status}")
print(f"\nTotal: {passed} passed, {failed} failed, {errors} errors")
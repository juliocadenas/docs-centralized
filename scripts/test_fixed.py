#!/usr/bin/env python3
"""Test all 3 fixed services now."""
import requests, sys, struct, zlib, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = "http://100.105.27.27:9000/v1"

def make_png(w=4, h=4, color=b'\xff\x00\x00'):
    raw = b''
    for y in range(h):
        raw += b'\x00'
        for x in range(w):
            raw += color
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))

png = make_png()

# Wait for effects service to load
time.sleep(3)

# 1. Test Rembg via Gateway
print("=== Rembg via Gateway ===")
r = requests.post(f"{BASE}/effects/remove-bg", files={"file": ("test.png", png, "image/png")}, timeout=60)
print(f"  HTTP {r.status_code}: {len(r.content)} bytes")
if r.status_code != 200:
    print(f"  Body: {r.text[:200]}")
else:
    print("  ✅ REMBG WORKING!")

# 2. Test Upscale via Gateway
print("\n=== Upscale via Gateway ===")
r = requests.post(f"{BASE}/effects/upscale", files={"file": ("test.png", png, "image/png")}, data={"scale": 2}, timeout=120)
print(f"  HTTP {r.status_code}: {len(r.content)} bytes")
if r.status_code != 200:
    print(f"  Body: {r.text[:200]}")
else:
    print("  ✅ UPSCALE WORKING!")

# 3. Test ComfyUI directly (bypass Gateway to isolate issue)
print("\n=== ComfyUI direct workflow test ===")
import json
workflow = {
    "3": {"class_type": "KSampler", "inputs": {"cfg": 7.0, "denoise": 1.0, "latent_image": ["5", 0], "model": ["4", 0], "negative": ["7", 0], "positive": ["6", 0], "sampler_name": "euler", "scheduler": "normal", "seed": 42, "steps": 5}},
    "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": 256, "width": 256}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": "a cute robot"}},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": "blurry, bad"}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "AIHub_test", "images": ["8", 0]}}
}
r = requests.post("http://100.105.27.27:8188/prompt", json={"prompt": workflow}, timeout=30)
print(f"  HTTP {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  ✅ ComfyUI accepted! prompt_id: {data.get('prompt_id', 'N/A')}")
else:
    print(f"  Error: {r.text[:300]}")

# 4. Test ComfyUI via Gateway
print("\n=== ComfyUI via Gateway ===")
r = requests.post(f"{BASE}/images/generations", json={
    "model": "sd15",
    "prompt": "a cute robot",
    "n": 1,
    "size": "256x256"
}, timeout=60)
print(f"  HTTP {r.status_code}: {r.text[:200]}")
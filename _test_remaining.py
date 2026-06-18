"""Test remaining online endpoints: images, audio gen, portrait, models."""
import httpx
import time

GW = "http://100.105.27.27:9000/v1"
results = {}

# 1. Models endpoint
print("[1] GET /v1/models")
try:
    r = httpx.get(f"{GW}/models", timeout=10)
    if r.status_code == 200:
        data = r.json()
        models = data.get("data", [])
        print(f"  [OK] {len(models)} models listed")
        for m in models[:5]:
            print(f"    - {m.get('id','?')}")
        results["models"] = "PASS"
    else:
        print(f"  [FAIL] {r.status_code}")
        results["models"] = "FAIL"
except Exception as e:
    print(f"  [FAIL] {e}")
    results["models"] = "FAIL"

# 2. Status endpoint
print("\n[2] GET /v1/status")
try:
    r = httpx.get(f"{GW}/status", timeout=10)
    if r.status_code == 200:
        services = r.json().get("services", [])
        online = [s for s in services if s.get("status") == "online"]
        print(f"  [OK] {len(online)}/{len(services)} services online")
        results["status"] = "PASS"
    else:
        print(f"  [FAIL] {r.status_code}")
        results["status"] = "FAIL"
except Exception as e:
    print(f"  [FAIL] {e}")
    results["status"] = "FAIL"

# 3. Image generation (ComfyUI)
print("\n[3] POST /v1/images/generations")
try:
    r = httpx.post(f"{GW}/images/generations",
        json={
            "prompt": "a simple red circle on white background",
            "n": 1,
            "size": "512x512"
        }, timeout=120)
    if r.status_code == 200:
        data = r.json()
        imgs = data.get("data", [])
        if imgs:
            b64 = imgs[0].get("b64_json", "")
            print(f"  [OK] Image generated, b64 length={len(b64)}")
            results["images"] = "PASS"
        else:
            print(f"  [FAIL] No image in response")
            results["images"] = "FAIL"
    else:
        print(f"  [FAIL] {r.status_code}: {r.text[:200]}")
        results["images"] = "FAIL"
except Exception as e:
    print(f"  [FAIL] {e}")
    results["images"] = "FAIL"

# 4. Audio generation (DocuMusic)
print("\n[4] POST /v1/audio/generations")
try:
    r = httpx.post(f"{GW}/audio/generations",
        json={
            "prompt": "calm piano music, 10 seconds",
            "duration_seconds": 10
        }, timeout=180)
    if r.status_code == 200:
        ct = r.headers.get("content-type", "?")
        print(f"  [OK] Audio generated, {len(r.content)} bytes, type={ct}")
        results["audio_gen"] = "PASS"
    else:
        print(f"  [FAIL] {r.status_code}: {r.text[:200]}")
        results["audio_gen"] = "FAIL"
except Exception as e:
    print(f"  [FAIL] {e}")
    results["audio_gen"] = "FAIL"

# 5. Infrastructure endpoint
print("\n[5] GET /v1/infrastructure")
try:
    r = httpx.get(f"{GW}/infrastructure", timeout=10)
    if r.status_code == 200:
        print(f"  [OK] Infrastructure data returned")
        results["infra"] = "PASS"
    else:
        print(f"  [FAIL] {r.status_code}")
        results["infra"] = "FAIL"
except Exception as e:
    print(f"  [FAIL] {e}")
    results["infra"] = "FAIL"

# Summary
print("\n" + "=" * 50)
print("RESULTS")
print("=" * 50)
for k, v in results.items():
    icon = "[OK]" if v == "PASS" else "[XX]"
    print(f"  {icon} {k}")
passed = sum(1 for v in results.values() if v == "PASS")
print(f"\n  {passed}/{len(results)} passed")
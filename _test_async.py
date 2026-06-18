"""Test async image + audio generation with polling."""
import httpx
import time

GW = "http://100.105.27.27:9000/v1"

# 1. Image generation with polling
print("=== Image Generation (async) ===")
r = httpx.post(f"{GW}/images/generations",
    json={"prompt": "a red circle on white background", "n": 1, "size": "512x512"}, timeout=30)
data = r.json()
prompt_id = data.get("id")
print(f"  Submitted: {prompt_id}")
print(f"  Status URL: {data.get('check_status')}")

# Poll for image
for i in range(12):  # up to 60s
    time.sleep(5)
    r = httpx.get(f"{GW}/images/status/{prompt_id}", timeout=15)
    data = r.json()
    status = data.get("status")
    print(f"  [{i*5}s] status={status}")
    if status == "completed":
        imgs = data.get("data", data.get("images", []))
        if imgs:
            url = imgs[0].get("url", "") if isinstance(imgs[0], dict) else str(imgs[0])
            b64 = imgs[0].get("b64_json", "") if isinstance(imgs[0], dict) else ""
            print(f"  [OK] Image ready! url={url[:80]}, b64_len={len(b64)}")
        else:
            print(f"  [OK] Keys: {list(data.keys())}")
            print(f"  Full: {str(data)[:300]}")
        break
    elif status == "error" or status == "failed":
        print(f"  [FAIL] {data}")
        break

# 2. Audio generation with polling
print("\n=== Audio Generation (async) ===")
r = httpx.post(f"{GW}/audio/generations",
    json={"prompt": "calm piano, 5 seconds", "duration_seconds": 5}, timeout=30)
data = r.json()
audio_id = data.get("id")
print(f"  Submitted: {audio_id}")

# Poll for audio
for i in range(12):
    time.sleep(5)
    r = httpx.get(f"{GW}/audio/status/{audio_id}", timeout=15)
    data = r.json()
    status = data.get("status")
    url = data.get("audio_url")
    print(f"  [{i*5}s] status={status}, url={'yes' if url else 'no'}")
    if status == "completed" and url:
        print(f"  [OK] Audio ready! url={url[:80]}")
        # Download it
        if url.startswith("http"):
            r2 = httpx.get(url, timeout=30)
            print(f"  Downloaded: {len(r2.content)} bytes")
        break
    elif status in ("error", "failed"):
        print(f"  [FAIL] {data}")
        break
"""Debug images + audio gen responses."""
import httpx
import json

GW = "http://100.105.27.27:9000/v1"

# 1. Images - see full response
print("=== Images full response ===")
r = httpx.post(f"{GW}/images/generations",
    json={"prompt": "a red circle", "n": 1, "size": "512x512"}, timeout=120)
print(f"Status: {r.status_code}")
print(f"CT: {r.headers.get('content-type')}")
print(f"Body: {r.text[:1000]}")

# 2. Audio gen - see full response
print("\n=== Audio gen full response ===")
r = httpx.post(f"{GW}/audio/generations",
    json={"prompt": "calm piano, 5 seconds", "duration_seconds": 5}, timeout=180)
print(f"Status: {r.status_code}")
print(f"CT: {r.headers.get('content-type')}")
print(f"Body: {r.text[:1000]}")

# 3. Check images router schema
print("\n=== Images router ===")
r = httpx.get(f"{GW}/openapi.json", timeout=10)
data = r.json()
for path in ["/v1/images/generations", "/images/generations"]:
    if path in data.get("paths", {}):
        post = data["paths"][path].get("post", {})
        body = post.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        print(f"  {path}: {body}")
        ref = body.get("$ref", "")
        if ref:
            sn = ref.split("/")[-1]
            sd = data.get("components", {}).get("schemas", {}).get(sn, {})
            print(f"  Properties: {list(sd.get('properties', {}).keys())}")
            print(f"  Required: {sd.get('required', [])}")
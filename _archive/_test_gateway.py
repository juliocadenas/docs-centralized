"""Live end-to-end test of AI Hub Gateway."""
import httpx
import sys

BASE = "http://100.105.27.27:9000/v1"

print("=== AI Hub Gateway Live Test ===")
print()

# Test 1: Status
print("[1] GET /v1/status")
try:
    r = httpx.get(f"{BASE}/status", timeout=15)
    data = r.json()
    gpu = data.get("gpu", {})
    print(f"    GPU: {gpu.get('name','?')} | VRAM: {gpu.get('vram_used_pct','?')}%")
    services = data.get("services", {})
    print(f"    Services: {len(services)} registered")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 2: Models
print()
print("[2] GET /v1/models")
try:
    r = httpx.get(f"{BASE}/models", timeout=15)
    data = r.json()
    models = data.get("data", [])
    print(f"    Total models: {len(models)}")
    for m in models[:8]:
        print(f"    - {m.get('id','?')}")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 3: Chat (LLM)
print()
print("[3] POST /v1/chat/completions (llama3.1)")
try:
    r = httpx.post(
        f"{BASE}/chat/completions",
        json={
            "model": "llama3.1",
            "messages": [{"role": "user", "content": "Say hello in 3 words"}],
            "stream": False,
            "max_tokens": 30,
        },
        timeout=60,
    )
    data = r.json()
    msg = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(f"    Response: {msg[:100]}")
except Exception as e:
    print(f"    FAIL: {e}")

print()
print("=== All tests complete ===")
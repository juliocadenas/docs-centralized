"""Option A: End-to-end AI stack verification."""
import requests
import json
import sys
import time

GATEWAY = "http://100.105.27.27:9000"

def main():
    print("=" * 60)
    print("  AI STACK END-TO-END VERIFICATION")
    print("=" * 60)
    print()

    # 1. Check Gateway status
    print("[1/5] Checking Gateway /v1/status...")
    try:
        r = requests.get(f"{GATEWAY}/v1/status", timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"  OK - Status: {r.status_code}")
            print(f"  GPU: {data.get('gpu', 'N/A')}")
            print(f"  Models loaded: {data.get('models_loaded', data.get('active_models', 'N/A'))}")
        else:
            print(f"  WARN - Status code: {r.status_code}")
    except Exception as e:
        print(f"  FAIL: {e}")
        return

    print()

    # 2. List available models
    print("[2/5] Listing models via /v1/models...")
    try:
        r = requests.get(f"{GATEWAY}/v1/models", timeout=10)
        if r.status_code == 200:
            data = r.json()
            models = data.get("data", [])
            print(f"  OK - {len(models)} models available")
            for m in models[:5]:
                print(f"    - {m.get('id', 'N/A')}")
        else:
            print(f"  WARN - Status: {r.status_code}")
            print(f"  Body: {r.text[:200]}")
    except Exception as e:
        print(f"  FAIL: {e}")
        return

    print()

    # 3. Chat completion test
    print("[3/5] Testing /v1/chat/completions (LLM)...")
    try:
        payload = {
            "model": "llama3.1:latest",
            "messages": [{"role": "user", "content": "Say 'AI Hub is operational' in exactly 5 words"}],
            "max_tokens": 20,
            "temperature": 0.1,
            "stream": False
        }
        r = requests.post(f"{GATEWAY}/v1/chat/completions", json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"  OK - Response: {content.strip()}")
        else:
            print(f"  WARN - Status: {r.status_code}")
            print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  FAIL: {e}")

    print()

    # 4. Infrastructure endpoint
    print("[4/5] Checking /v1/infrastructure...")
    try:
        r = requests.get(f"{GATEWAY}/v1/infrastructure", timeout=10)
        if r.status_code == 200:
            print(f"  OK - Infrastructure endpoint working")
        else:
            print(f"  WARN - Status: {r.status_code}")
    except Exception as e:
        print(f"  FAIL: {e}")

    print()

    # 5. GPU memory check
    print("[5/5] Checking GPU memory after test...")
    try:
        r = requests.get(f"{GATEWAY}/v1/status", timeout=10)
        if r.status_code == 200:
            data = r.json()
            gpu_info = str(data.get("gpu", ""))
            print(f"  GPU status: {gpu_info[:200]}")
    except Exception as e:
        print(f"  FAIL: {e}")

    print()
    print("=" * 60)
    print("  END-TO-END VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
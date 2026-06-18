"""Check actual API endpoints of STT and Effects backends."""
import httpx

print("=== Backend API Discovery ===\n")

# STT on :8020
print("[STT :8020]")
for path in ["/", "/docs", "/openapi.json", "/transcribe", "/api/transcribe", "/v1/transcribe", "/predict"]:
    try:
        r = httpx.get(f"http://100.105.27.27:8020{path}", timeout=5)
        print(f"  GET {path:30s} -> {r.status_code}")
    except:
        print(f"  GET {path:30s} -> ERROR")

# Rembg on :8050
print("\n[Rembg :8050]")
for path in ["/", "/docs", "/openapi.json", "/api/remove", "/remove", "/api/remove-bg", "/process", "/predict"]:
    try:
        r = httpx.get(f"http://100.105.27.27:8050{path}", timeout=5)
        print(f"  GET {path:30s} -> {r.status_code}")
    except:
        print(f"  GET {path:30s} -> ERROR")

# Upscale on :8051
print("\n[Upscale :8051]")
for path in ["/", "/docs", "/openapi.json", "/api/upscale", "/upscale", "/process", "/predict"]:
    try:
        r = httpx.get(f"http://100.105.27.27:8051{path}", timeout=5)
        print(f"  GET {path:30s} -> {r.status_code}")
    except:
        print(f"  GET {path:30s} -> ERROR")

# If openapi.json exists on any, get the actual paths
for port_name, port in [("STT", 8020), ("Rembg", 8050), ("Upscale", 8051)]:
    try:
        r = httpx.get(f"http://100.105.27.27:{port}/openapi.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            paths = list(data.get("paths", {}).keys())
            print(f"\n[{port_name} openapi paths]: {paths}")
    except:
        pass
"""Get openapi schemas for Rembg, Upscale, and STT."""
import httpx

for name, port in [("STT", 8020), ("Rembg", 8050), ("Upscale", 8051)]:
    print(f"\n=== {name} :{port} openapi ===")
    r = httpx.get(f"http://100.105.27.27:{port}/openapi.json", timeout=10)
    data = r.json()
    for path, methods in data.get("paths", {}).items():
        for method, info in methods.items():
            print(f"  {method.upper()} {path}")
            req_body = info.get("requestBody", {})
            if req_body:
                content = req_body.get("content", {})
                for ct, schema in content.items():
                    print(f"    Content-Type: {ct}")
                    ref = schema.get("$ref", schema.get("schema", {}).get("$ref", ""))
                    print(f"    Schema: {ref}")
            params = info.get("parameters", [])
            for p in params:
                print(f"    Param: {p.get('name')} ({p.get('in')})")
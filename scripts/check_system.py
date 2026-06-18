#!/usr/bin/env python3
"""
AI Hub Madrid - System Monitor
Run: python scripts/check_system.py

Quick health check for the entire AI stack.
Connects to the Gateway API and reports status.
"""
import requests
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GATEWAY = "http://100.105.27.27:9000/v1"


def check_system():
    print("=" * 60)
    print("  AI HUB MADRID - System Monitor")
    print("=" * 60)

    # 1. Gateway status
    try:
        r = requests.get(f"{GATEWAY}/status", timeout=10)
        if r.status_code != 200:
            print(f"  [FAIL] Gateway unreachable (HTTP {r.status_code})")
            return False
        data = r.json()
    except Exception as e:
        print(f"  [FAIL] Gateway unreachable: {e}")
        return False

    status = data["status"].upper()
    gpu = data["gpu"]
    vram_pct = gpu["used_vram_mb"] * 100 // gpu["total_vram_mb"]
    uptime_min = data["uptime_seconds"] // 60

    status_emoji = "[ OK ]" if status == "OK" else "[WARN]"
    print(f"\n  Gateway:    {status_emoji} {status}")
    print(f"  Uptime:     {uptime_min:.0f} min")
    print(f"  VRAM:       {gpu['used_vram_mb']}MB / {gpu['total_vram_mb']}MB ({vram_pct}%)")

    # VRAM safety check
    if vram_pct > 80:
        print(f"  [CRIT] VRAM usage > 80% - risk of OOM!")
    elif vram_pct > 60:
        print(f"  [WARN] VRAM usage > 60% - monitor closely")

    # 2. Services
    print(f"\n  Services:")
    online = 0
    offline = 0
    for svc in sorted(data["services"], key=lambda s: s["name"]):
        if svc["status"] == "online":
            print(f"    OK   {svc['name']:30s} :{svc['port']}")
            online += 1
        else:
            print(f"    --   {svc['name']:30s} :{svc['port']} (idle/lazy)")
            offline += 1

    print(f"\n  Total: {online} online, {offline} idle/lazy-load")

    # 3. Quick LLM test
    print(f"\n  Testing LLM (Ollama)...")
    try:
        r = requests.post(f"{GATEWAY}/chat/completions", json={
            "model": "llama3.1:latest",
            "messages": [{"role": "user", "content": "Respond with just: OK"}],
            "max_tokens": 5,
            "stream": False
        }, timeout=30)
        if r.status_code == 200:
            reply = r.json()["choices"][0]["message"]["content"].strip()
            print(f"    [ OK ] LLM responded: '{reply}'")
        else:
            print(f"    [FAIL] LLM HTTP {r.status_code}")
    except Exception as e:
        print(f"    [FAIL] LLM error: {e}")

    # 4. Summary
    print(f"\n{'=' * 60}")
    if status == "OK" and vram_pct < 80:
        print(f"  RESULT: ALL GOOD - System is healthy")
    elif vram_pct >= 80:
        print(f"  RESULT: WARNING - High VRAM usage")
    else:
        print(f"  RESULT: DEGRADED - Check services")
    print(f"{'=' * 60}")
    return True


if __name__ == "__main__":
    check_system()
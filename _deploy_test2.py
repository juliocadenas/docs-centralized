"""Deploy + verify field names + re-test."""
import os
import sys
import io
import struct
import wave
import time as time_mod

try:
    import paramiko
except ImportError:
    os.system(f"{sys.executable} -m pip install paramiko -q")
    import paramiko

import httpx

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
BASE = os.path.dirname(os.path.abspath(__file__))
GW = "http://100.105.27.27:9000/v1"

# Step 1: Check schema field names from backends
print("=== Step 1: Check backend schemas ===")
for name, port in [("Rembg", 8050), ("Upscale", 8051)]:
    r = httpx.get(f"http://100.105.27.27:{port}/openapi.json", timeout=10)
    data = r.json()
    schemas = data.get("components", {}).get("schemas", {})
    for sname, sdef in schemas.items():
        if "Body" in sname:
            props = sdef.get("properties", {})
            print(f"  {name} schema '{sname}': fields={list(props.keys())}")

# Step 2: Deploy fixes
print("\n=== Step 2: Deploy fixes ===")
FILES = [
    ("ai-hub-gateway/gateway/routers/voice.py",   "/mnt/seagate/ai-hub-gateway/gateway/routers/voice.py"),
    ("ai-hub-gateway/gateway/routers/effects.py", "/mnt/seagate/ai-hub-gateway/gateway/routers/effects.py"),
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)
sftp = ssh.open_sftp()

for local_rel, remote_path in FILES:
    local_path = os.path.join(BASE, local_rel.replace("/", os.sep))
    sftp.put(local_path, remote_path)
    print(f"  [OK] {local_rel}")

sftp.close()

# Restart gateway
stdin, stdout, stderr = ssh.exec_command(f"echo '{PASS}' | sudo -S systemctl restart ai-hub-gateway 2>&1")
stdout.channel.recv_exit_status()
time_mod.sleep(3)
stdin, stdout, stderr = ssh.exec_command("systemctl is-active ai-hub-gateway")
status = stdout.read().decode().strip()
print(f"  Gateway status: {status}")
ssh.close()

# Step 3: Re-test
print("\n=== Step 3: Re-test endpoints ===")

# STT
print("[1] STT")
try:
    sample_rate = 16000
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack("<" + "h" * sample_rate, *([0] * sample_rate)))
    wav_buffer.seek(0)
    r = httpx.post(f"{GW}/audio/transcriptions",
        files={"file": ("test.wav", wav_buffer, "audio/wav")},
        data={"language": "es"}, timeout=60)
    if r.status_code == 200:
        print(f"    [OK] text: '{r.json().get('text','')[:50]}'")
    else:
        print(f"    [FAIL] {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"    [FAIL] {e}")

# Effects with different image URL (not Wikipedia)
print("[2] RemoveBG (direct file upload)")
try:
    # Create a tiny test PNG
    import zlib
    # Minimal 1x1 red PNG
    png_bytes = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000"
        "00907753de0000000c4944415408d76360f8cf000000ffff030004"
        "5d1e63040000000049454e44ae426082"
    )
    r = httpx.post(f"{GW}/effects/remove-bg",
        files={"file": ("test.png", png_bytes, "image/png")},
        timeout=30)
    if r.status_code == 200:
        print(f"    [OK] {len(r.content)} bytes, type={r.headers.get('content-type','?')}")
    else:
        print(f"    [FAIL] {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"    [FAIL] {e}")

print("[3] Upscale (direct file upload)")
try:
    r = httpx.post(f"{GW}/effects/upscale",
        files={"file": ("test.png", png_bytes, "image/png")},
        data={"scale": "2"},
        timeout=60)
    if r.status_code == 200:
        print(f"    [OK] {len(r.content)} bytes, type={r.headers.get('content-type','?')}")
    else:
        print(f"    [FAIL] {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"    [FAIL] {e}")

print("\n=== Done ===")
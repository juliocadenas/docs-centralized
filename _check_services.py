"""Check which AI services are running on the server."""
import paramiko
import socket

SERVER = "100.105.27.27"

# Services to check (name, port, systemd_service)
SERVICES = [
    ("Ollama (LLM)", 11434, "ollama"),
    ("ComfyUI (Image)", 8188, "comfyui"),
    ("DocuMusic", 8000, None),
    ("Wan2GP (Video)", 7860, "wan2gp"),
    ("Piper TTS", 8010, "tts"),
    ("Whisper STT", 8020, "stt"),
    ("MuseTalk", 8041, "musetalk"),
    ("LatentSync", 8043, "latentsync"),
    ("LivePortrait", 8044, "liveportrait"),
    ("Hallo2", 8070, "hallo2"),
    ("Rembg (Effects)", 8050, "effects"),
    ("Upscale", 8051, "effects"),
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username="pepe", password="pepe1234", timeout=10)

def run(cmd):
    _, o, _ = ssh.exec_command(cmd, timeout=15)
    return o.read().decode(errors="replace").strip()

print("=" * 65)
print("  AI SERVICES STATUS")
print("=" * 65)
print()
print(f"{'Service':<25} {'Port':<8} {'Systemd':<15} {'Port Open':<10}")
print("-" * 65)

for name, port, svc in SERVICES:
    # Check port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    port_open = sock.connect_ex((SERVER, port)) == 0
    sock.close()

    # Check systemd
    if svc:
        status = run(f"systemctl is-active {svc} 2>/dev/null || echo 'not-found'")
    else:
        status = "docker?"

    port_str = "OPEN" if port_open else "closed"
    print(f"{name:<25} {port:<8} {status:<15} {port_str:<10}")

# Also check docker containers
print()
print("Docker containers:")
docker = run("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>&1")
print(docker if docker else "  (none)")

# Check systemd services for AI
print()
print("Systemd AI services:")
systemd = run("systemctl list-units --type=service --all 2>/dev/null | grep -iE 'ollama|comfy|muse|latent|live|hall|effect|tts|stt|wan|piper|whisper|ai-hub|rembg|upscale' || echo '(none found)'")
print(systemd)

# VRAM status
print()
print("GPU VRAM:")
vram = run("nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader 2>&1")
print(f"  {vram}")

# Processes using GPU
print()
print("GPU processes:")
procs = run("nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>&1")
print(f"  {procs if procs else '(no GPU processes)'}")

ssh.close()
print()
print("=" * 65)
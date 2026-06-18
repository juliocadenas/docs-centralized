#!/bin/bash
echo "=== ACTIVE PORTS ==="
for p in 9000 3000 7860 8188 8000 8010 8020 8041 8044 8050 8051; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://localhost:$p 2>/dev/null)
    echo "  :$p -> HTTP $code"
done
echo ""
echo "=== SYSTEMD SERVICES ==="
systemctl list-units --type=service --state=running 2>/dev/null | grep -E "ai-hub|tts|stt|ollama|wan|comfy|musetalk|liveportrait|effects|avatar"
echo ""
echo "=== GPU ==="
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
#!/bin/bash
# Instalar Hallo2, LatentSync, LivePortrait, MuseTalk en NAB9
set -e
cd /mnt/seagate

# 1. Clonar repos
echo "=== Clonando repos ==="
test -d LatentSync || git clone https://github.com/bytedance/LatentSync.git
test -d LivePortrait || git clone https://github.com/KwaiVGI/LivePortrait.git
test -d MuseTalk || git clone https://github.com/TMElyralab/MuseTalk.git

# 2. Instalar dependencias
echo "=== Instalando dependencias ==="
PIP=/home/pepe/comfyui_env/bin/pip
for repo in LatentSync LivePortrait MuseTalk hallo2; do
    test -f $repo/requirements.txt && $PIP install -r $repo/requirements.txt 2>&1 | tail -3
done

# 3. Descargar modelos (placeholder)
echo "=== Modelos ==="
mkdir -p /mnt/seagate/models/hallo2 /mnt/seagate/models/latentsync /mnt/seagate/models/liveportrait /mnt/seagate/models/musetalk
echo "Model dirs creadas"

# 4. Crear apps Gradio
echo "=== Creando apps Gradio ==="
cd /home/pepe
$PIP install gradio 2>&1 | tail -3

# Hallo2 puerto 8070
nohup /home/pepe/comfyui_env/bin/python hallo2_app.py > /tmp/hallo2.log 2>&1 &
echo "Hallo2 PID: $!"
sleep 2

# LatentSync puerto 8043
nohup /home/pepe/comfyui_env/bin/python latentsync_app.py > /tmp/latentsync.log 2>&1 &
echo "LatentSync PID: $!"
sleep 2

# LivePortrait puerto 8044
nohup /home/pepe/comfyui_env/bin/python liveportrait_app.py > /tmp/liveportrait.log 2>&1 &
echo "LivePortrait PID: $!"
sleep 2

# MuseTalk puerto 8040
nohup /home/pepe/comfyui_env/bin/python musetalk_app.py > /tmp/musetalk.log 2>&1 &
echo "MuseTalk PID: $!"
sleep 2

echo "=== Verificacion ==="
for port in 8070 8043 8044 8040; do
    code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port 2>/dev/null || echo "FAIL")
    echo "Puerto $port: HTTP $code"
done

echo "=== Instalacion completada ==="
#!/bin/bash
# Instalar Hallo2 en NAB9
set -e
cd /mnt/seagate/hallo2

echo "=== Instalando dependencias ==="
pip install -r requirements.txt 2>&1 | tail -5

echo "=== Descargando modelos ==="
python scripts/download_models.py 2>&1 || echo "Intentando manual..."
# Modelos necesarios de HuggingFace
mkdir -p pretrained_models
pip install huggingface_hub 2>&1

python3 << 'PYEOF'
from huggingface_hub import snapshot_download
# Modelos de Hallo2
snapshot_download("fudan-generative-ai/hallo2", local_dir="pretrained_models")
print("Modelos descargados OK")
PYEOF

echo "=== Creando Gradio app ==="
cat > /mnt/seagate/hallo2/gradio_app.py << 'GRADIO'
import gradio as gr
import torch
import sys
sys.path.insert(0, '/mnt/seagate/hallo2')
from hallo.pipelines import Hallo2Pipeline

pipeline = Hallo2Pipeline.from_pretrained("pretrained_models")
pipeline.to("cuda" if torch.cuda.is_available() else "cpu")

def generate(source_image, driving_audio, steps=25, guidance=3.5):
    video = pipeline(
        source_image=source_image,
        driving_audio=driving_audio,
        num_inference_steps=steps,
        guidance_scale=guidance,
    )
    return video

demo = gr.Interface(
    fn=generate,
    inputs=[
        gr.Image(type="filepath", label="Foto de la persona"),
        gr.Audio(type="filepath", label="Audio de voz"),
        gr.Slider(10, 50, 25, label="Steps"),
        gr.Slider(1.0, 7.0, 3.5, label="Guidance"),
    ],
    outputs=gr.Video(label="Video del avatar hablando"),
    title="Hallo2 - Avatar Hablando",
    description="Sube una foto + audio y genera un video del avatar hablando"
)
demo.launch(server_name="0.0.0.0", server_port=8070, share=False)
GRADIO

echo "=== Iniciando Hallo2 Gradio en puerto 8070 ==="
nohup python /mnt/seagate/hallo2/gradio_app.py > /tmp/hallo2.log 2>&1 &
echo "PID: $!"
sleep 3
curl -s -o /dev/null -w '%{http_code}' http://localhost:8070
echo " - Hallo2 iniciado"
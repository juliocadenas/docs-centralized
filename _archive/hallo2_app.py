"""Hallo2 Gradio App - Avatar Hablando (Equivalente a HeyGen)"""
import gradio as gr
import sys, os

sys.path.insert(0, '/mnt/seagate/hallo2')
HAVE_MODEL = False
pipeline = None

try:
    from hallo.pipelines import Hallo2Pipeline
    pipeline = Hallo2Pipeline.from_pretrained('/mnt/seagate/models/hallo2')
    pipeline.to('cuda')
    HAVE_MODEL = True
    print("Hallo2 pipeline loaded on CUDA")
except Exception as e:
    print(f"Hallo2 not ready: {e}")

def generate(source_image, driving_audio, steps=25, guidance=3.5):
    if not HAVE_MODEL:
        return None
    return pipeline(
        source_image=source_image,
        driving_audio=driving_audio,
        num_inference_steps=int(steps),
        guidance_scale=guidance,
    )

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
    description="Sube una foto + audio y genera un video del avatar hablando. Equivalente a HeyGen.",
    allow_flagging="never",
)
demo.launch(server_name="0.0.0.0", server_port=8070, share=False)
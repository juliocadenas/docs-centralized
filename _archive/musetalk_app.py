"""MuseTalk Gradio App - Lip-sync en tiempo real (Equivalente a HeyGen Live)"""
import gradio as gr
import sys, os

sys.path.insert(0, '/mnt/seagate/MuseTalk')
HAVE_MODEL = False
pipeline = None

try:
    from musetalk import MuseTalk
    pipeline = MuseTalk.from_pretrained('/mnt/seagate/models/musetalk')
    pipeline.to('cuda')
    HAVE_MODEL = True
    print("MuseTalk pipeline loaded on CUDA")
except Exception as e:
    print(f"MuseTalk not ready: {e}")

def generate(face_image, audio_file):
    if not HAVE_MODEL:
        return None
    return pipeline(face_image=face_image, audio_file=audio_file)

demo = gr.Interface(
    fn=generate,
    inputs=[
        gr.Image(type="filepath", label="Foto de la cara"),
        gr.Audio(type="filepath", label="Audio de voz"),
    ],
    outputs=gr.Video(label="Video con lip-sync"),
    title="MuseTalk - Lip-sync en Tiempo Real",
    description="Lip-sync en tiempo real con pipeline de avatar hablando. Equivalente a HeyGen Live.",
    allow_flagging="never",
)
demo.launch(server_name="0.0.0.0", server_port=8040, share=False)
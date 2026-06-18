"""LatentSync Gradio App - Lip-sync Perfecto (Equivalente a HeyGen Lip-sync)"""
import gradio as gr
import sys, os

sys.path.insert(0, '/mnt/seagate/LatentSync')
HAVE_MODEL = False
pipeline = None

try:
    from pipelines import LatentSyncPipeline
    pipeline = LatentSyncPipeline.from_pretrained('/mnt/seagate/models/latentsync')
    pipeline.to('cuda')
    HAVE_MODEL = True
    print("LatentSync pipeline loaded on CUDA")
except Exception as e:
    print(f"LatentSync not ready: {e}")

def generate(face_image, audio_file, guidance=2.0, steps=25):
    if not HAVE_MODEL:
        return None
    return pipeline(
        face_image=face_image,
        audio_file=audio_file,
        guidance_scale=guidance,
        num_inference_steps=int(steps),
    )

demo = gr.Interface(
    fn=generate,
    inputs=[
        gr.Image(type="filepath", label="Foto de la cara"),
        gr.Audio(type="filepath", label="Audio de voz"),
        gr.Slider(1.0, 7.0, 2.0, label="Guidance"),
        gr.Slider(10, 50, 25, label="Steps"),
    ],
    outputs=gr.Video(label="Video con lip-sync"),
    title="LatentSync - Lip-sync Perfecto",
    description="Sincronizacion labios perfecta con difusion. Equivalente a HeyGen Lip-sync.",
    allow_flagging="never",
)
demo.launch(server_name="0.0.0.0", server_port=8043, share=False)
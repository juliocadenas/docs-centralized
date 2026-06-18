"""LivePortrait Gradio App - Anima fotos (Equivalente a HeyGen Express)"""
import gradio as gr
import sys, os

sys.path.insert(0, '/mnt/seagate/LivePortrait')
HAVE_MODEL = False
pipeline = None

try:
    from pipelines import LivePortraitPipeline
    pipeline = LivePortraitPipeline.from_pretrained('/mnt/seagate/models/liveportrait')
    pipeline.to('cuda')
    HAVE_MODEL = True
    print("LivePortrait pipeline loaded on CUDA")
except Exception as e:
    print(f"LivePortrait not ready: {e}")

def animate(source_image, driving_video=None):
    if not HAVE_MODEL:
        return None
    return pipeline(source_image=source_image, driving_video=driving_video)

demo = gr.Interface(
    fn=animate,
    inputs=[
        gr.Image(type="filepath", label="Foto a animar"),
        gr.Video(type="filepath", label="Video de referencia (opcional)"),
    ],
    outputs=gr.Video(label="Foto animada"),
    title="LivePortrait - Anima tus fotos",
    description="Anima fotos con expresiones faciales naturales. Equivalente a HeyGen Express.",
    allow_flagging="never",
)
demo.launch(server_name="0.0.0.0", server_port=8044, share=False)
"""Fix Hallo2 gradio compat + check LivePortrait/MuseTalk."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=120):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:400] if err else "")

def write_remote(path, content):
    sftp = s.open_sftp()
    with sftp.open(path, 'w') as f:
        f.write(content)
    sftp.close()

# ============================================================
# 1. Fix Hallo2 - remove allow_flagging (gradio 5.x compat)
# ============================================================
print("=== Fix Hallo2 wrapper ===")
hallo2_fixed = '''"""Hallo2 Gradio App - Avatar Hablando"""
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
    description="Sube una foto + audio y genera un video del avatar hablando.",
)
demo.launch(server_name="0.0.0.0", server_port=8070, share=False)
'''
write_remote("/home/pepe/hallo2_app.py", hallo2_fixed)
print("  Wrapper fixed (removed allow_flagging)")

# Restart Hallo2
print(run("echo pepe1234 | sudo -S systemctl restart hallo2 2>&1"))
time.sleep(15)
h2 = run("systemctl is-active hallo2 2>&1")
print(f"  Hallo2: {h2}")
if "active" not in h2:
    print(run("journalctl -u hallo2 --no-pager -n 8 2>&1"))
    run("echo pepe1234 | sudo -S systemctl stop hallo2 2>&1")

# ============================================================
# 2. Check MuseTalk - went from online to unknown
# ============================================================
print("\n=== MuseTalk check ===")
print(f"  systemd: {run('systemctl is-active musetalk 2>&1')}")
print(f"  port: {run('curl -s -o /dev/null -w ' + chr(39) + '%{http_code}' + chr(39) + ' http://localhost:8041/ 2>&1')}")
print(run("journalctl -u musetalk --no-pager -n 5 --since '2 min ago' 2>&1"))

# ============================================================
# 3. Check LivePortrait - old process may have died
# ============================================================
print("\n=== LivePortrait check ===")
lp_code = run("curl -s -o /dev/null -w " + chr(39) + "%{http_code}" + chr(39) + " http://localhost:8044/ 2>&1")
print(f"  port 8044: {lp_code}")
if lp_code != "200":
    # Old process died, restart via systemd
    print("  Restarting via systemd...")
    print(run("echo pepe1234 | sudo -S systemctl enable liveportrait 2>&1"))
    print(run("echo pepe1234 | sudo -S systemctl start liveportrait 2>&1"))
    time.sleep(20)
    lp2 = run("curl -s -o /dev/null -w " + chr(39) + "%{http_code}" + chr(39) + " http://localhost:8044/ 2>&1")
    print(f"  port 8044 after restart: {lp2}")
    if lp2 != "200":
        print(run("journalctl -u liveportrait --no-pager -n 10 2>&1"))

# ============================================================
# 4. Final count
# ============================================================
print("\n=== Final Status ===")
status_raw = run("curl -s http://localhost:9000/v1/status")
if status_raw:
    import json
    try:
        d = json.loads(status_raw)
        online = sum(1 for sv in d.get("services", []) if sv.get("status") == "online")
        total = len(d.get("services", []))
        print(f"  Online: {online}/{total}")
        for sv in d.get("services", []):
            mark = "OK" if sv.get("status") == "online" else "XX"
            print(f"    [{mark}] {sv.get('name','?'):30s} {sv.get('status','?'):10s} :{sv.get('port','?')}")
    except Exception as ex:
        print(f"  Error: {ex}")

s.close()
print("\nDone!")
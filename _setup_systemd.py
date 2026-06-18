"""Create systemd services for all offline services + fix MuseTalk + update Gateway config."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=120):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:500] if err else "")

def write_remote(path, content):
    """Write file to remote server."""
    sftp = s.open_sftp()
    with sftp.open(path, 'w') as f:
        f.write(content)
    sftp.close()

# ============================================================
# 1. First check where effects_service_real.py is running from
# ============================================================
print("=== Find effects process ===")
print(run("ps aux | grep effects | grep -v grep"))
print(run("find /home/pepe /mnt/seagate -maxdepth 2 -name 'effects_service_real.py' 2>/dev/null"))

# ============================================================
# 2. Fix MuseTalk systemd - use correct app.py from repo
# ============================================================
print("\n=== Fix MuseTalk systemd ===")
musetalk_svc = """[Unit]
Description=MuseTalk Lip-Sync (Gradio)
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/mnt/seagate/MuseTalk
ExecStart=/home/pepe/ai_env/bin/python app.py --ip 0.0.0.0 --port 8041
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
write_remote("/tmp/musetalk.service", musetalk_svc)
print(run("echo pepe1234 | sudo -S cp /tmp/musetalk.service /etc/systemd/system/musetalk.service && echo pepe1234 | sudo -S systemctl daemon-reload 2>&1"))

# ============================================================
# 3. Create LatentSync systemd - use gradio_app.py from repo
# ============================================================
print("\n=== Create LatentSync systemd ===")
latentsync_svc = """[Unit]
Description=LatentSync Lip-Sync (Gradio)
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/mnt/seagate/LatentSync
ExecStart=/home/pepe/ai_env/bin/python gradio_app.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
write_remote("/tmp/latentsync.service", latentsync_svc)
print(run("echo pepe1234 | sudo -S cp /tmp/latentsync.service /etc/systemd/system/latentsync.service && echo pepe1234 | sudo -S systemctl daemon-reload 2>&1"))

# ============================================================
# 4. Create LivePortrait systemd (replace nohup)
# ============================================================
print("\n=== Create LivePortrait systemd ===")
liveportrait_svc = """[Unit]
Description=LivePortrait Avatar Animation (Gradio)
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/mnt/seagate/LivePortrait
ExecStart=/home/pepe/ai_env/bin/python app.py --server_port 8044 --server_name 0.0.0.0
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
write_remote("/tmp/liveportrait.service", liveportrait_svc)
print(run("echo pepe1234 | sudo -S cp /tmp/liveportrait.service /etc/systemd/system/liveportrait.service && echo pepe1234 | sudo -S systemctl daemon-reload 2>&1"))

# Kill the existing nohup process
print(run("kill 394978 2>&1 || echo 'already stopped'"))
time.sleep(3)

# ============================================================
# 5. Create Hallo2 systemd - use real app from repo
# ============================================================
print("\n=== Create Hallo2 systemd ===")
# Check for Hallo2's real entry point
print(run("find /mnt/seagate/hallo2 -name 'app.py' -o -name 'inference.py' -o -name 'run*.py' | head -5 2>&1"))
print(run("ls /mnt/seagate/hallo2/hallo/ 2>&1"))

hallo2_svc = """[Unit]
Description=Hallo2 Avatar (Gradio)
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/mnt/seagate/hallo2
ExecStart=/home/pepe/ai_env/bin/python /home/pepe/hallo2_app.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
write_remote("/tmp/hallo2.service", hallo2_svc)
print(run("echo pepe1234 | sudo -S cp /tmp/hallo2.service /etc/systemd/system/hallo2.service && echo pepe1234 | sudo -S systemctl daemon-reload 2>&1"))

# ============================================================
# 6. Create Effects systemd (rembg + esrgan + higgsfield)
# ============================================================
print("\n=== Create Effects systemd ===")
# Find the running effects script
effects_path = run("readlink -f /proc/1687561/exe 2>&1 || echo ''")
print(f"Effects process exe: {effects_path}")
effects_cwd = run("readlink -f /proc/1687561/cwd 2>&1 || echo ''")
print(f"Effects process cwd: {effects_cwd}")

effects_svc = """[Unit]
Description=Effects Services (Rembg + Real-ESRGAN)
After=network.target

[Service]
Type=simple
User=pepe
WorkingDirectory=/home/pepe
ExecStart=/home/pepe/ai_env/bin/python effects_services.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
write_remote("/tmp/effects.service", effects_svc)
print(run("echo pepe1234 | sudo -S cp /tmp/effects.service /etc/systemd/system/effects.service && echo pepe1234 | sudo -S systemctl daemon-reload 2>&1"))

# ============================================================
# 7. Try starting MuseTalk and LatentSync, capture errors
# ============================================================
print("\n=== Try start MuseTalk ===")
print(run("echo pepe1234 | sudo -S systemctl start musetalk 2>&1"))
time.sleep(15)
status = run("systemctl is-active musetalk 2>&1")
print(f"MuseTalk: {status}")
if "active" not in status:
    print(run("journalctl -u musetalk --no-pager -n 15 --since '1 min ago' 2>&1"))
    print(run("echo pepe1234 | sudo -S systemctl stop musetalk 2>&1"))

print("\n=== Try start LatentSync ===")
print(run("echo pepe1234 | sudo -S systemctl start latentsync 2>&1"))
time.sleep(15)
status = run("systemctl is-active latentsync 2>&1")
print(f"LatentSync: {status}")
if "active" not in status:
    print(run("journalctl -u latentsync --no-pager -n 15 --since '1 min ago' 2>&1"))
    print(run("echo pepe1234 | sudo -S systemctl stop latentsync 2>&1"))

print("\n=== Try start LivePortrait ===")
print(run("echo pepe1234 | sudo -S systemctl start liveportrait 2>&1"))
time.sleep(15)
status = run("systemctl is-active liveportrait 2>&1")
print(f"LivePortrait: {status}")
if "active" not in status:
    print(run("journalctl -u liveportrait --no-pager -n 15 --since '1 min ago' 2>&1"))

s.close()
print("\nDone!")
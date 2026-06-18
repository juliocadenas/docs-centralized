"""Diagnose the 4 offline services: MuseTalk, LatentSync, Hallo2, Higgsfield."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=60):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:300] if err else "")

services = [
    ("MuseTalk", "/mnt/seagate/MuseTalk", "/mnt/seagate/MuseTalk/venv", 8041, "musetalk"),
    ("LatentSync", "/mnt/seagate/LatentSync", "/mnt/seagate/LatentSync/venv", 8043, None),
    ("LivePortrait", "/mnt/seagate/LivePortrait", "/mnt/seagate/LivePortrait/venv", 8044, None),
    ("Hallo2", "/mnt/seagate/hallo2", "/mnt/seagate/hallo2/venv", 8070, None),
]

for name, path, venv, port, sd in services:
    print(f"\n{'='*60}")
    print(f"  {name} (:{port})")
    print(f"{'='*60}")
    print(f"  Path: {run('ls -d ' + path + ' 2>&1')}")
    print(f"  Venv: {run('ls ' + venv + '/bin/python 2>&1')}")
    torch_cmd = venv + '/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available())" 2>&1'
    print(f"  Torch: {run(torch_cmd)}")
    if sd:
        print(f"  Systemd: {run('cat /etc/systemd/system/' + sd + '.service 2>&1 | head -10')}")
    else:
        print(f"  Systemd: {run('ls /etc/systemd/system/*' + name.lower() + '* 2>&1')}")

print(f"\n{'='*60}")
print("  Processes running")
print(f"{'='*60}")
print(run("ps aux | grep -E 'avatar|musetalk|latentsync|liveportrait|hallo2|higgsfield|effects' | grep -v grep"))

print(f"\n{'='*60}")
print("  Effects service")
print(f"{'='*60}")
print(run("ls /etc/systemd/system/effects* 2>&1"))
print(run("systemctl is-active effects 2>&1"))
print(run("head -30 /home/pepe/effects_services.py 2>&1"))

s.close()
print("\nDone!")
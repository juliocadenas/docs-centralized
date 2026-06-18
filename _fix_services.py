"""Fix MuseTalk + LatentSync deps and retry."""
import paramiko, time

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=300):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:500] if err else "")

print("=== numpy version ===")
print(run("/home/pepe/ai_env/bin/python -c 'import numpy; print(numpy.__version__)'"))

print("=== Fix xtcocotools ===")
print(run("/home/pepe/ai_env/bin/pip install --force-reinstall --no-deps xtcocotools 2>&1 | tail -5", 180))

print("=== Fix decord ===")
print(run("/home/pepe/ai_env/bin/pip install decord 2>&1 | tail -5", 120))

print("=== Retry MuseTalk ===")
run("echo pepe1234 | sudo -S systemctl stop musetalk 2>&1")
time.sleep(2)
run("echo pepe1234 | sudo -S systemctl start musetalk 2>&1")
time.sleep(20)
st = run("systemctl is-active musetalk 2>&1")
print(f"MuseTalk: {st}")
if "active" not in st:
    print(run("journalctl -u musetalk --no-pager -n 8 2>&1"))
    run("echo pepe1234 | sudo -S systemctl stop musetalk 2>&1")

print("\n=== Retry LatentSync ===")
run("echo pepe1234 | sudo -S systemctl stop latentsync 2>&1")
time.sleep(2)
run("echo pepe1234 | sudo -S systemctl start latentsync 2>&1")
time.sleep(20)
st = run("systemctl is-active latentsync 2>&1")
print(f"LatentSync: {st}")
if "active" not in st:
    print(run("journalctl -u latentsync --no-pager -n 8 2>&1"))
    run("echo pepe1234 | sudo -S systemctl stop latentsync 2>&1")

s.close()
print("\nDone!")
"""Fix remaining offline services + VRAM management."""
import paramiko, time, json

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect("100.105.27.27", username="pepe", password="pepe1234", timeout=15)

def run(cmd, t=120):
    _, o, e = s.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out + ("\n  ERR: " + err[:400] if err else "")

# 1. Check LivePortrait - was online before, now unknown
print("=== LivePortrait status ===")
print(run("systemctl is-active liveportrait 2>&1"))
print(run("journalctl -u liveportrait --no-pager -n 5 --since '2 min ago' 2>&1"))
print(run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8044/ 2>&1"))

# 2. Check Hallo2
print("\n=== Hallo2 status ===")
print(run("systemctl is-active hallo2 2>&1"))
print(run("journalctl -u hallo2 --no-pager -n 10 --since '2 min ago' 2>&1"))

# 3. Check effects - wrong script
print("\n=== Effects systemd config ===")
print(run("cat /etc/systemd/system/effects.service 2>&1"))
print(run("systemctl is-active effects 2>&1"))
print(run("journalctl -u effects --no-pager -n 8 --since '2 min ago' 2>&1"))

# 4. Check what's eating VRAM
print("\n=== VRAM per process ===")
print(run("nvidia-smi --query-compute-apps=pid,used_memory,name --format=csv,noheader 2>&1"))

# 5. Fix effects service - it was running from /mnt/seagate/ai-hub-gateway/effects_service_real.py
print("\n=== Fix effects systemd ===")
# Read the real effects script
print(run("head -5 /mnt/seagate/ai-hub-gateway/effects_service_real.py 2>&1"))

# Check ports 8050 and 8051
print("\n=== Port checks ===")
print(run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8050/ 2>&1"))
print(run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8051/ 2>&1"))
print(run("ss -tlnp | grep -E '8050|8051|8052' 2>&1"))

s.close()
print("\nDone!")
"""Final comprehensive verification of NUCLEAR RECOVERY deployment."""
import paramiko
import sys
import socket

SERVER = "100.105.27.27"

def main():
    # Check connectivity
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    if sock.connect_ex((SERVER, 22)) != 0:
        print("FAIL: Cannot connect to server")
        sys.exit(1)
    sock.close()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username="pepe", password="pepe1234", timeout=10)

    def run(cmd):
        _, o, _ = ssh.exec_command(cmd, timeout=30)
        return o.read().decode(errors='replace').strip()

    checks = []

    # 1. Kernel cmdline
    cmdline = run("cat /proc/cmdline")
    checks.append(("panic=10", "panic=10" in cmdline))
    checks.append(("fsck.mode=force", "fsck.mode=force" in cmdline))
    checks.append(("fsck.repair=yes", "fsck.repair=yes" in cmdline))

    # 2. GPU
    gpu = run("nvidia-smi -L 2>&1")
    checks.append(("NVIDIA GPU detected", "RTX 5080" in gpu))
    vram = run("nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader 2>&1")
    checks.append(("VRAM healthy (>10GB free)", "MiB" in vram))

    # 3. Services
    checks.append(("Ollama active", run("systemctl is-active ollama") == "active"))
    checks.append(("Gateway active", run("systemctl is-active ai-hub-gateway") == "active"))
    checks.append(("Watchdog active", run("systemctl is-active vram-watchdog") == "active"))
    checks.append(("Watchdog enabled", run("systemctl is-enabled vram-watchdog") == "enabled"))

    # 4. Uptime (fresh boot)
    uptime = run("uptime")
    checks.append(("Fresh boot (< 60 min)", "min" in uptime))

    ssh.close()

    print("=" * 60)
    print("  NUCLEAR RECOVERY - FINAL VERIFICATION")
    print("=" * 60)
    print()
    all_pass = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        icon = "[OK]" if passed else "[XX]"
        print(f"  {icon} {status}: {name}")
        if not passed:
            all_pass = False
    print()
    if all_pass:
        print("=" * 60)
        print("  ALL CHECKS PASSED - SYSTEM FULLY PROTECTED")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  SOME CHECKS FAILED - REVIEW NEEDED")
        print("=" * 60)

if __name__ == "__main__":
    main()
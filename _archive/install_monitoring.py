"""
Install monitoring, backup, and security on the AI Hub server.
Uploads health_check.sh, backup.sh, sets up cron, and configures firewall.
"""
import subprocess
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SERVER = "julio@100.105.27.27"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


def main():
    print("=" * 60)
    print("  AI Hub Madrid - Install Monitoring & Security")
    print("=" * 60)

    # Step 1: Upload scripts
    print("\n[1/4] Uploading scripts...")
    run(f'ssh {SERVER} "mkdir -p /mnt/seagate/scripts /mnt/seagate/logs /mnt/seagate/backups"')
    run(f'scp "{BASE_DIR}\\health_check.sh" {SERVER}:/mnt/seagate/scripts/')
    run(f'scp "{BASE_DIR}\\backup.sh" {SERVER}:/mnt/seagate/scripts/')
    run(f'ssh {SERVER} "chmod +x /mnt/seagate/scripts/health_check.sh /mnt/seagate/scripts/backup.sh"')
    print("  Scripts uploaded.")

    # Step 2: Install cron jobs
    print("\n[2/4] Setting up cron jobs...")
    cron_setup = (
        f"ssh {SERVER} '"
        '(crontab -l 2>/dev/null | grep -v health_check; echo "*/5 * * * * /mnt/seagate/scripts/health_check.sh") | crontab - ; '
        '(crontab -l 2>/dev/null | grep -v backup.sh; echo "0 3 * * 0 /mnt/seagate/scripts/backup.sh") | crontab - ; '
        "echo installed; crontab -l'"
    )
    ok, out, err = run(cron_setup)
    print(f"  {out}")

    # Step 3: Configure firewall (Tailscale + LAN only)
    print("\n[3/4] Configuring firewall...")
    firewall_setup = (
        f"ssh {SERVER} '"
        "which ufw >/dev/null 2>&1 || sudo apt-get install -y ufw 2>/dev/null; "
        "sudo ufw --force reset >/dev/null 2>&1; "
        "sudo ufw default deny incoming; "
        "sudo ufw default allow outgoing; "
        "sudo ufw allow 22/tcp; "
        "sudo ufw allow in on tailscale0; "
        "sudo ufw allow from 192.168.1.0/24 to any port 9000 proto tcp; "
        "sudo ufw --force enable; "
        "echo Firewall done'"
    )
    ok, out, err = run(firewall_setup)
    print(f"  {out}" if ok else f"  {err}")

    # Step 4: Run initial health check
    print("\n[4/4] Running initial health check...")
    ok, out, err = run(
        f'ssh {SERVER} "bash /mnt/seagate/scripts/health_check.sh && tail -5 /mnt/seagate/logs/health_check.log"'
    )
    print(f"  {out}")

    print("\n" + "=" * 60)
    print("  Installation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
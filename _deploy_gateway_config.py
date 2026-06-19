"""Upload config.py to NAB9 and restart ai-hub-gateway."""
import paramiko

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"
LOCAL = r"ai-hub-gateway\gateway\config.py"
REMOTE = "/mnt/seagate/ai-hub-gateway/gateway/config.py"

def main():
    print("=== Connecting to NAB9 ===")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()

    print(f"=== Uploading {LOCAL} -> {REMOTE} ===")
    sftp.put(LOCAL, REMOTE)
    sftp.close()
    print("  Upload done.")

    print("=== Restarting ai-hub-gateway ===")
    stdin, stdout, stderr = client.exec_command("sudo -S systemctl restart ai-hub-gateway", timeout=30)
    stdin.write(PASS + "\n")
    stdin.flush()
    out = stdout.read().decode()
    err = stderr.read().decode()
    rc = stdout.channel.recv_exit_status()
    if out: print(out)
    if err: print(err)

    if rc == 0:
        print("GATEWAY_RESTARTED OK")
    else:
        print(f"ERROR: exit code {rc}")

    # Verify
    print("=== Verifying ===")
    stdin, stdout, stderr = client.exec_command("sleep 3 && curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/v1/status", timeout=15)
    out = stdout.read().decode()
    print(f"Gateway status: HTTP {out}")

    client.close()
    print("DONE")

if __name__ == "__main__":
    main()
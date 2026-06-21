#!/usr/bin/env python3
"""Test SSH connection to NAB9."""
import paramiko
import sys
import traceback

OUTPUT_FILE = "_ssh_test.txt"

def main():
    lines = []
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Try multiple usernames and keys
    users = ["pepe", "julio", "root"]
    keys = [
        "C:/Users/julio/.ssh/id_ed25519",
        "C:/Users/julio/.ssh/id_rsa",
    ]
    
    connected = False
    for user in users:
        for key in keys:
            try:
                lines.append(f"Trying {user}@100.105.27.27 with key={key}...")
                ssh.connect(
                    "100.105.27.27",
                    username=user,
                    key_filename=key,
                    timeout=15,
                    allow_agent=False,
                    look_for_keys=False,
                )
                lines.append(f"  SUCCESS! Connected as {user} with {key}")
                
                # Run commands
                stdin, stdout, stderr = ssh.exec_command("hostname")
                hostname = stdout.read().decode().strip()
                lines.append(f"  hostname: {hostname}")
                
                stdin, stdout, stderr = ssh.exec_command("whoami")
                whoami = stdout.read().decode().strip()
                lines.append(f"  whoami: {whoami}")
                
                stdin, stdout, stderr = ssh.exec_command("df -h /mnt/seagate 2>/dev/null || echo 'N/A'")
                df = stdout.read().decode().strip()
                lines.append(f"  seagate: {df}")
                
                connected = True
                ssh.close()
                break
            except paramiko.AuthenticationException as e:
                lines.append(f"  Auth failed: {e}")
            except Exception as e:
                lines.append(f"  Error: {e}")
        if connected:
            break
    
    if not connected:
        lines.append("\nAll connection attempts failed!")
        lines.append("Need password authentication or key setup.")
    
    result = "\n".join(lines)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(result)
    print(result)

if __name__ == "__main__":
    main()
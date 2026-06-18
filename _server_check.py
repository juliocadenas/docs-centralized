"""Check server via multiple methods - Tailscale, LAN, ping."""
import socket, subprocess, time

# Try pinging Tailscale IP
print("=== PING Tailscale IP ===")
result = subprocess.run(["ping", "-n", "3", "100.105.27.27"], capture_output=True, text=True, timeout=15)
print(result.stdout)

# Try LAN IP
print("\n=== PING LAN IP ===")
result = subprocess.run(["ping", "-n", "3", "192.168.1.42"], capture_output=True, text=True, timeout=15)
print(result.stdout)

# Try Gateway port 9000 on Tailscale
print("\n=== Check Gateway Port 9000 ===")
for ip in ["100.105.27.27", "192.168.1.42"]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, 9000))
        sock.close()
        print(f"  {ip}:9000 -> {'OPEN' if result == 0 else f'CLOSED ({result})'}")
    except Exception as ex:
        print(f"  {ip}:9000 -> Error: {ex}")

# Try SSH on LAN
print("\n=== Check SSH Port 22 ===")
for ip in ["100.105.27.27", "192.168.1.42"]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, 22))
        sock.close()
        print(f"  {ip}:22 -> {'OPEN' if result == 0 else f'CLOSED ({result})'}")
    except Exception as ex:
        print(f"  {ip}:22 -> Error: {ex}")

print("\n=== DIAGNOSIS ===")
print("If all ports are CLOSED, the server is stuck in busybox initramfs.")
print("This is the ROOT CAUSE of the periodic crashes!")
print("The server needs PHYSICAL intervention:")
print("  1. Connect monitor+keyboard to NAB9")
print("  2. Check initramfs console for error messages")
print("  3. Usually: 'fsck' needs to run on root filesystem")
print("  4. Or: /dev/sdaX not found - disk controller issue")
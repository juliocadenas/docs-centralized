#!/usr/bin/env python3
"""Deep audit of NAB9 - single SSH batch command for speed."""
import paramiko, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PASS = "pepe1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password=PASS, timeout=20)

# Build a single bash script that runs ALL commands at once on the server
# This avoids the latency of 20 separate SSH round-trips
batch_script = r'''
echo "=====START_AUDIT====="

echo "===SECTION:PARTITIONS==="
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT 2>/dev/null

echo "===SECTION:ROOT_DEV==="
findmnt -n -o SOURCE,TARGET,FSTYPE,OPTIONS / 2>/dev/null

echo "===SECTION:FSTAB==="
cat /etc/fstab 2>/dev/null

echo "===SECTION:CMDLINE==="
cat /proc/cmdline 2>/dev/null

echo "===SECTION:KERNELSTUB==="
cat /etc/kernelstub/configuration 2>/dev/null || echo "NOT_FOUND"

echo "===SECTION:EFI_LS==="
ls /boot/efi/EFI/ 2>/dev/null

echo "===SECTION:EFI_CMDLINE_FILES==="
find /boot/efi/EFI/ -name cmdline 2>/dev/null | while read f; do echo "FILE:$f"; cat "$f"; echo ""; done

echo "===SECTION:INITRAMFS_PREMOUNT==="
ls -la /etc/initramfs-tools/scripts/init-premount/ 2>/dev/null || echo "EMPTY"

echo "===SECTION:INITRAMFS_BOTTOM==="
ls -la /etc/initramfs-tools/scripts/init-bottom/ 2>/dev/null || echo "EMPTY"

echo "===SECTION:KERNEL==="
uname -r

echo "===SECTION:INITRAMFS_BINS==="
KVER=$(uname -r)
for binary in fsck e2fsck blkid reboot sync grep awk cat sleep; do
    R=$(lsinitramfs /boot/initrd.img-$KVER 2>/dev/null | grep -w "${binary}$" | head -1)
    if [ -n "$R" ]; then echo "$binary:FOUND:$R"; else echo "$binary:MISSING"; fi
done

echo "===SECTION:NVIDIA_SMI==="
nvidia-smi 2>&1 | head -20

echo "===SECTION:NVIDIA_LSMOD==="
lsmod | grep -i nvidia || echo "NVIDIA_MODULE_NOT_LOADED"

echo "===SECTION:NVIDIA_LSPCI==="
lspci | grep -i nvidia || echo "NO_NVIDIA_PCI"

echo "===SECTION:SERVICES_INSTALLED==="
systemctl list-unit-files --type=service 2>/dev/null | grep -iE "comfy|wan|docu|muse|latent|live|hallo|effect|ollama|gateway|tts|stt|rembg|upscale|vram" || echo "NONE"

echo "===SECTION:SERVICES_RUNNING==="
systemctl list-units --type=service --state=running 2>/dev/null | grep -iE "comfy|wan|docu|muse|latent|live|hallo|effect|ollama|gateway|tts|stt|rembg|upscale|vram" || echo "NONE_RUNNING"

echo "===SECTION:SMART==="
echo pepe1234 | sudo -S smartctl -H /dev/sda 2>/dev/null || echo "SMARTCTL_UNAVAILABLE"

echo "===SECTION:DISK_MODEL==="
lsblk -d -o NAME,MODEL,SIZE,ROTA,TYPE 2>/dev/null

echo "===SECTION:FS_TYPE==="
df -Th / 2>/dev/null

echo "===SECTION:MOUNT_ROOT==="
mount | grep " on / " 2>/dev/null

echo "===SECTION:INITRAMFS_SIZE==="
ls -lh /boot/initrd.img-* 2>/dev/null

echo "===SECTION:CRONTAB_USER==="
crontab -l 2>/dev/null || echo "NO_USER_CRONTAB"

echo "===SECTION:CRONTAB_ROOT==="
echo pepe1234 | sudo -S crontab -l 2>/dev/null || echo "NO_ROOT_CRONTAB"

echo "===SECTION:UPTIME==="
uptime

echo "===SECTION:MEMORY==="
free -h

echo "===SECTION:TUNE2FS==="
ROOT_DEV=$(findmnt -n -o SOURCE / 2>/dev/null)
echo "Root: $ROOT_DEV"
echo pepe1234 | sudo -S tune2fs -l "$ROOT_DEV" 2>/dev/null | grep -iE "mount count|maximum mount|state|error" || echo "tune2fs failed"

echo "===SECTION:GPU_PROCS==="
nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv,noheader 2>/dev/null || echo "NO_GPU_PROCS"

echo "===SECTION:DMESG_ERRORS==="
echo pepe1234 | sudo -S dmesg --level=err,crit,alert,emerg 2>/dev/null | tail -10 || echo "NO_ERRORS"

echo "=====END_AUDIT====="
'''

print("Running audit (single batch SSH command)...")
_, stdout, _ = ssh.exec_command(batch_script, timeout=30)
stdout.channel.set_combine_stderr(True)
output = stdout.read().decode('utf-8', errors='replace')

# Filter password prompts
lines = output.split('\n')
clean_lines = [l for l in lines if '[sudo]' not in l and 'password for pepe' not in l.lower()]
output = '\n'.join(clean_lines)

print(output)

# Save to file for reference
with open('_audit_results.txt', 'w', encoding='utf-8') as f:
    f.write(output)

ssh.close()
print("\n\nAudit saved to _audit_results.txt")
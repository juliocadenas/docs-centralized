#!/usr/bin/env python3
"""Direct fix: upload a shell script to server and execute it.
Avoids all Python-to-bash quoting issues."""
import paramiko, sys, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PASS = "pepe1234"
HOST = "100.105.27.27"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='pepe', password=PASS, timeout=20)

# Shell script that fixes everything
fix_script = r'''#!/bin/bash
set -e
echo "=====FIX SCRIPT START====="

# 1. Check what scripts exist in initramfs
echo "===CHECK_INITRAMFS_SCRIPTS==="
KVER=$(uname -r)
echo "Kernel: $KVER"
echo ""
echo "--- auto-fsck ---"
lsinitramfs /boot/initrd.img-$KVER 2>/dev/null | grep auto-fsck || echo "NOT FOUND"
echo ""
echo "--- panic-guard ---"
lsinitramfs /boot/initrd.img-$KVER 2>/dev/null | grep panic-guard || echo "NOT FOUND"
echo ""
echo "--- all custom scripts ---"
lsinitramfs /boot/initrd.img-$KVER 2>/dev/null | grep -E "zz-auto|zz-panic|init-premount|init-bottom" || echo "NONE"

# 2. Check initramfs-tools scripts directory
echo ""
echo "===INITRAMFS_TOOLS_SCRIPTS==="
echo "--- init-premount ---"
ls -la /etc/initramfs-tools/scripts/init-premount/ 2>/dev/null
echo ""
echo "--- init-bottom ---"
ls -la /etc/initramfs-tools/scripts/init-bottom/ 2>/dev/null

# 3. Check kernelstub config
echo ""
echo "===KERNELSTUB_CONFIG==="
cat /etc/kernelstub/configuration

# 4. Run kernelstub with verbose output
echo ""
echo "===RUN_KERNELSTUB==="
kernelstub -v 2>&1 || echo "kernelstub exit code: $?"

# 5. Check EFI cmdline after kernelstub
echo ""
echo "===EFI_CMDLINE_AFTER==="
find /boot/efi/EFI/ -name cmdline 2>/dev/null | while read f; do
    echo "FILE: $f"
    cat "$f"
    echo ""
done

# 6. Check if we need to manually update EFI cmdline
echo ""
echo "===EFI_CMDLINE_FILES==="
find /boot/efi/EFI/ -name cmdline 2>/dev/null

# 7. tune2fs verification
echo ""
echo "===TUNE2FS_VERIFY==="
tune2fs -l /dev/sda3 2>/dev/null | grep -E "Mount count|Maximum mount|Filesystem state|Errors behavior"

# 8. VRAM watchdog status
echo ""
echo "===VRAM_WATCHDOG==="
systemctl is-active vram-watchdog 2>/dev/null
systemctl is-enabled vram-watchdog 2>/dev/null

# 9. Services status
echo ""
echo "===SERVICES_STATUS==="
for svc in comfyui wan2gp musetalk latentsync liveportrait hallo2 effects ai-hub-effects avatar avatar_services tts stt; do
    echo "$svc: $(systemctl is-enabled $svc 2>/dev/null) / $(systemctl is-active $svc 2>/dev/null)"
done

echo ""
echo "===OLLAMA_GATEWAY==="
echo "ollama: $(systemctl is-enabled ollama 2>/dev/null) / $(systemctl is-active ollama 2>/dev/null)"
echo "ai-hub-gateway: $(systemctl is-enabled ai-hub-gateway 2>/dev/null) / $(systemctl is-active ai-hub-gateway 2>/dev/null)"

# 10. Sysctl
echo ""
echo "===SYSCTL==="
sysctl kernel.panic kernel.panic_on_oops 2>/dev/null

# 11. NVIDIA
echo ""
echo "===NVIDIA==="
nvidia-smi -L 2>&1 || echo "nvidia-smi FAILED"

echo "=====FIX SCRIPT END====="
'''

# Upload script
print("Uploading fix script to server...")
sftp = ssh.open_sftp()
with sftp.file('/tmp/nuclear_fix.sh', 'w') as f:
    f.write(fix_script)
sftp.chmod('/tmp/nuclear_fix.sh', 0o755)
sftp.close()

# Execute
print("Running diagnostics...\n")
stdin, stdout, stderr = ssh.exec_command(f'echo {PASS} | sudo -S bash /tmp/nuclear_fix.sh 2>&1', timeout=60)
output = stdout.read().decode('utf-8', errors='replace')

# Filter sudo prompt
lines = [l for l in output.split('\n') if '[sudo]' not in l and 'password for pepe' not in l.lower()]
print('\n'.join(lines))

# Now check if kernelstub needs manual EFI update
print("\n" + "=" * 60)
print("ANALYSIS:")
print("=" * 60)

# If EFI cmdline doesn't have panic=10, we need to add it manually
if 'panic=10' not in output.split('===EFI_CMDLINE_AFTER===')[1].split('===')[0] if '===EFI_CMDLINE_AFTER===' in output else True:
    print("\n⚠️  kernelstub did NOT update EFI cmdline!")
    print("   Need to manually update EFI cmdline file.")

    # Find and update EFI cmdline files
    efi_fix = r'''#!/bin/bash
# Find all EFI cmdline files and add our params
echo "===MANUAL_EFI_UPDATE==="
find /boot/efi/EFI/ -name cmdline 2>/dev/null | while read f; do
    echo "Updating: $f"
    echo "BEFORE:"
    cat "$f"

    # Backup
    cp "$f" "${f}.bak.$(date +%Y%m%d%H%M%S)"

    # Read current content and add missing params
    CONTENT=$(cat "$f")

    # Add panic=10 if missing
    if ! echo "$CONTENT" | grep -q "panic=10"; then
        CONTENT="$CONTENT panic=10"
    fi

    # Add fsck.mode=force if missing
    if ! echo "$CONTENT" | grep -q "fsck.mode=force"; then
        CONTENT="$CONTENT fsck.mode=force"
    fi

    # Add fsck.repair=yes if missing
    if ! echo "$CONTENT" | grep -q "fsck.repair=yes"; then
        CONTENT="$CONTENT fsck.repair=yes"
    fi

    # Write back
    echo "$CONTENT" > "$f"
    echo "AFTER:"
    cat "$f"
    echo ""
done
echo "===DONE==="
'''

    sftp = ssh.open_sftp()
    with sftp.file('/tmp/efi_fix.sh', 'w') as f:
        f.write(efi_fix)
    sftp.chmod('/tmp/efi_fix.sh', 0o755)
    sftp.close()

    print("\nRunning manual EFI cmdline update...")
    _, stdout2, _ = ssh.exec_command(f'echo {PASS} | sudo -S bash /tmp/efi_fix.sh 2>&1', timeout=30)
    output2 = stdout2.read().decode('utf-8', errors='replace')
    lines2 = [l for l in output2.split('\n') if '[sudo]' not in l and 'password for pepe' not in l.lower()]
    print('\n'.join(lines2))

# Check if panic-guard is missing from initramfs
if 'panic-guard' in output and 'NOT FOUND' in output.split('--- panic-guard ---')[1].split('---')[0]:
    print("\n⚠️  panic-guard NOT in initramfs!")
    print("   Checking if script exists in initramfs-tools...")

    panic_fix = r'''#!/bin/bash
echo "===PANIC_GUARD_CHECK==="
echo "Script file:"
ls -la /etc/initramfs-tools/scripts/init-bottom/zz-panic-guard 2>/dev/null || echo "MISSING"
echo ""
echo "Content:"
cat /etc/initramfs-tools/scripts/init-bottom/zz-panic-guard 2>/dev/null || echo "NO CONTENT"
echo ""

# If the file exists, check if it's executable and has proper shebang
if [ -f /etc/initramfs-tools/scripts/init-bottom/zz-panic-guard ]; then
    echo "File exists. Rebuilding initramfs..."
    update-initramfs -u -k $(uname -r) 2>&1 | tail -5
    echo ""
    echo "Verifying after rebuild:"
    lsinitramfs /boot/initrd.img-$(uname -r) 2>/dev/null | grep -E "panic-guard|init-bottom" || echo "STILL NOT FOUND"
fi
echo "===DONE==="
'''
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/panic_fix.sh', 'w') as f:
        f.write(panic_fix)
    sftp.chmod('/tmp/panic_fix.sh', 0o755)
    sftp.close()

    print("\nChecking panic-guard...")
    _, stdout3, _ = ssh.exec_command(f'echo {PASS} | sudo -S bash /tmp/panic_fix.sh 2>&1', timeout=120)
    output3 = stdout3.read().decode('utf-8', errors='replace')
    lines3 = [l for l in output3.split('\n') if '[sudo]' not in l and 'password for pepe' not in l.lower()]
    print('\n'.join(lines3))

# Final verification
print("\n" + "=" * 60)
print("FINAL STATUS CHECK")
print("=" * 60)

final_check = r'''#!/bin/bash
echo "===FINAL_CHECK==="

# EFI cmdline
echo "1. EFI cmdline params:"
EFI_FILE=$(find /boot/efi/EFI/ -name cmdline 2>/dev/null | head -1)
if [ -n "$EFI_FILE" ]; then
    if grep -q "panic=10" "$EFI_FILE"; then echo "   [PASS] panic=10 in EFI"; else echo "   [FAIL] panic=10 NOT in EFI"; fi
    if grep -q "fsck.mode=force" "$EFI_FILE"; then echo "   [PASS] fsck.mode=force in EFI"; else echo "   [FAIL] fsck.mode=force NOT in EFI"; fi
else
    echo "   [WARN] No EFI cmdline file found"
fi

# Initramfs scripts
echo ""
echo "2. Initramfs scripts:"
KVER=$(uname -r)
if lsinitramfs /boot/initrd.img-$KVER 2>/dev/null | grep -q "auto-fsck"; then echo "   [PASS] auto-fsck in initramfs"; else echo "   [FAIL] auto-fsck NOT in initramfs"; fi
if lsinitramfs /boot/initrd.img-$KVER 2>/dev/null | grep -q "panic-guard"; then echo "   [PASS] panic-guard in initramfs"; else echo "   [FAIL] panic-guard NOT in initramfs"; fi

# Watchdog
echo ""
echo "3. VRAM watchdog: $(systemctl is-active vram-watchdog 2>/dev/null) / $(systemctl is-enabled vram-watchdog 2>/dev/null)"

# Sysctl
echo ""
echo "4. Sysctl: panic=$(sysctl -n kernel.panic 2>/dev/null), panic_on_oops=$(sysctl -n kernel.panic_on_oops 2>/dev/null)"

# tune2fs
echo ""
echo "5. tune2fs:"
tune2fs -l /dev/sda3 2>/dev/null | grep "Maximum mount count"

# Services
echo ""
echo "6. Services:"
ENABLED_SVCS=""
for svc in comfyui wan2gp musetalk latentsync liveportrait hallo2 effects ai-hub-effects avatar avatar_services tts stt; do
    STATE=$(systemctl is-enabled $svc 2>/dev/null)
    if [ "$STATE" = "enabled" ]; then
        ENABLED_SVCS="$ENABLED_SVCS $svc"
    fi
done
if [ -z "$ENABLED_SVCS" ]; then
    echo "   [PASS] All heavy services disabled"
else
    echo "   [FAIL] Still enabled:$ENABLED_SVCS"
fi
echo "   ollama: $(systemctl is-active ollama 2>/dev/null)"
echo "   gateway: $(systemctl is-active ai-hub-gateway 2>/dev/null)"

# GPU
echo ""
echo "7. GPU: $(nvidia-smi -L 2>&1 | head -1)"

echo ""
echo "===REBOOT_REQUIRED===" 
echo "All changes require a REBOOT to take full effect:"
echo "  - New kernel cmdline params (panic=10, fsck.mode=force)"
echo "  - Initramfs scripts activation"
echo "  - GPU recovery from AER crash"
echo "===END==="
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/final_check.sh', 'w') as f:
    f.write(final_check)
sftp.chmod('/tmp/final_check.sh', 0o755)
sftp.close()

print("\nRunning final verification...\n")
_, stdout4, _ = ssh.exec_command(f'echo {PASS} | sudo -S bash /tmp/final_check.sh 2>&1', timeout=30)
output4 = stdout4.read().decode('utf-8', errors='replace')
lines4 = [l for l in output4.split('\n') if '[sudo]' not in l and 'password for pepe' not in l.lower()]
print('\n'.join(lines4))

# Cleanup temp files
ssh.exec_command(f'echo {PASS} | sudo -S rm -f /tmp/nuclear_fix.sh /tmp/efi_fix.sh /tmp/panic_fix.sh /tmp/final_check.sh 2>/dev/null')

ssh.close()
print("\n\nDone. Ready for reboot.")
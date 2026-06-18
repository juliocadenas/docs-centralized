#!/usr/bin/env python3
import paramiko, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=20)

def run(cmd):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

lines = []
lines.append('=== 1. BOOT ENTRY ===')
lines.append(run('echo pepe1234 | sudo -S cat /boot/efi/loader/entries/Pop_OS-current.conf 2>/dev/null'))
lines.append('=== 2. CMDLINE EFI ===')
lines.append(run('echo pepe1234 | sudo -S cat /boot/efi/EFI/Pop_OS-73b66df5-a1ca-428a-b006-fb8c396311ea/cmdline 2>/dev/null'))
lines.append('=== 3. INITRAMFS SCRIPT ===')
lines.append(run('echo pepe1234 | sudo -S ls -la /etc/initramfs-tools/scripts/init-premount/usb-ssd-recovery 2>/dev/null'))
lines.append('=== 4. INITRAMFS CONTENIDO ===')
lines.append(run('echo pepe1234 | sudo -S cat /etc/initramfs-tools/scripts/init-premount/usb-ssd-recovery 2>/dev/null'))
lines.append('=== 5. FSTAB ===')
lines.append(run('cat /etc/fstab'))
lines.append('=== 6. KERNELSTUB ===')
lines.append(run('cat /etc/kernelstub/configuration 2>/dev/null'))
lines.append('=== 7. MODPROBE ===')
lines.append(run('cat /etc/modprobe.d/usb-ssd-fix.conf 2>/dev/null'))
lines.append('=== 8. UDEV ===')
lines.append(run('cat /etc/udev/rules.d/90-ssd-usb.rules 2>/dev/null'))
lines.append('=== 9. TMPFILES ===')
lines.append(run('cat /etc/tmpfiles.d/usb-autosuspend.conf 2>/dev/null'))

result = '\n'.join(lines)
script_dir = os.path.dirname(os.path.abspath(__file__))
outpath = os.path.join(script_dir, 'PRE_REBOOT_CHECK.txt')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(result)
print('Guardado, {} chars'.format(len(result)))
ssh.close()
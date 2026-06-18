#!/usr/bin/env python3
"""Configurar kernel cmdline en Pop!_OS systemd-boot con USB autosuspend."""
import paramiko
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run_cmd(ssh, cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=20)
    print("CONECTADO!\n")

    # ===== 1. Examinar particion EFI con sudo =====
    print("=" * 60)
    print("1. EXAMINANDO PARTICION EFI")
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S find /boot/efi -type f 2>/dev/null | head -30")
    print(out)
    
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S ls -la /boot/efi/EFI/ 2>/dev/null")
    print(out)
    
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S ls -la /boot/efi/loader/ 2>/dev/null")
    print(out)

    # ===== 2. BUSCAR KERNELSTUB CONFIG =====
    print("=" * 60)
    print("2. KERNELSTUB CONFIG")
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S cat /etc/kernelstub/configuration 2>/dev/null")
    print(f"   Config: {out.strip()}")
    
    out, _ = run_cmd(ssh, "which kernelstub 2>/dev/null")
    print(f"   kernelstub path: {out.strip()}")
    
    out, _ = run_cmd(ssh, "dpkg -l | grep kernelstub 2>/dev/null")
    print(f"   Paquete: {out.strip()}")

    # ===== 3. EDITAR CONFIG DE KERNELSTUB =====
    print("\n" + "=" * 60)
    print("3. CONFIGURANDO KERNEL CMDLINE")

    # Metodo 1: Si kernelstub existe, usarlo
    out, _ = run_cmd(ssh, "which kernelstub 2>/dev/null")
    if out.strip():
        print("   Usando kernelstub...")
        out, err = run_cmd(ssh, "echo pepe1234 | sudo -S kernelstub -a 'usbcore.autosuspend=-1 usbcore.usbfs_memory_mb=0' 2>&1")
        print(f"   {out.strip()}")
        if err.strip():
            print(f"   err: {err.strip()[:200]}")
    else:
        print("   kernelstub no disponible, editando manualmente...")
        
        # Metodo 2: Editar directamente /etc/kernelstub/configuration
        out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S cat /etc/kernelstub/configuration 2>/dev/null")
        if out.strip():
            print(f"   Config actual:\n{out}")
            # Agregar parametros
            run_cmd(ssh, """echo pepe1234 | sudo -S bash -c '
CONFIG=/etc/kernelstub/configuration
cp "$CONFIG" "${CONFIG}.bak"
if grep -q "usbcore.autosuspend" "$CONFIG"; then
    echo "Ya tiene autosuspend"
else
    # Buscar la linea default y agregar
    sed -i "s/\\\"quiet loglevel=0 systemd.show_status=false splash nvidia-drm.modeset=1\\\"/\\\"quiet loglevel=0 systemd.show_status=false splash nvidia-drm.modeset=1 usbcore.autosuspend=-1 usbcore.usbfs_memory_mb=0\\\"/" "$CONFIG"
    echo "Config modificada"
fi
cat "$CONFIG"
' 2>&1""")
        else:
            # Metodo 3: Para UKI, usar /etc/default/kernel-cmdline o similar
            print("   Sin kernelstub config, probando metodo alternativo...")
            out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S find /etc -name '*kernel*' -o -name '*cmdline*' 2>/dev/null | head -10")
            print(f"   {out}")
            
            # Crear config manual
            run_cmd(ssh, """echo pepe1234 | sudo -S bash -c '
# Para systemd-boot UKI, usar /etc/kernel/cmdline
mkdir -p /etc/kernel
echo "root=UUID=73b66df5-a1ca-428a-b006-fb8c396311ea ro quiet loglevel=0 systemd.show_status=false splash nvidia-drm.modeset=1 usbcore.autosuspend=-1 usbcore.usbfs_memory_mb=0" > /etc/kernel/cmdline
echo "Creado /etc/kernel/cmdline"
cat /etc/kernel/cmdline
' 2>&1""")

    # ===== 4. CONFIGURAR MODPROBE PARA USB =====
    print("\n" + "=" * 60)
    print("4. CONFIGURANDO MODPROBE (garantiza autosuspend=-1 al cargar)")
    run_cmd(ssh, """echo pepe1234 | sudo -S bash -c '
cat > /etc/modprobe.d/usb-ssd-fix.conf << "EOF"
# Desactivar USB autosuspend permanentemente
options usbcore autosuspend=-1
EOF
echo "Modprobe config creado"
cat /etc/modprobe.d/usb-ssd-fix.conf
' 2>&1""")
    out, _ = run_cmd(ssh, "cat /etc/modprobe.d/usb-ssd-fix.conf 2>&1")
    print(f"   {out.strip()}")

    # ===== 5. CONFIGURAR TLP (si existe) =====
    print("\n" + "=" * 60)
    print("5. VERIFICANDO TLP")
    out, _ = run_cmd(ssh, "echo pepe1234 | sudo -S tlp-stat -c 2>/dev/null | head -5 || echo 'TLP no instalado'")
    print(f"   {out.strip()}")

    # ===== 6. CONFIGURAR SYSTEMD tmpfiles para autosuspend runtime =====
    print("\n" + "=" * 60)
    print("6. CONFIGURANDO tmpfiles.d para autosuspend persistente")
    run_cmd(ssh, """echo pepe1234 | sudo -S bash -c '
cat > /etc/tmpfiles.d/usb-autosuspend.conf << "EOF"
#    Path                   Mode UID  GID  Age Argument
w    /sys/module/usbcore/parameters/autosuspend - - - - -1
w    /sys/bus/usb/devices/2-4/power/control - - - - on
w    /sys/bus/usb/devices/*/power/control - - - - on
EOF
echo "tmpfiles.d config creado"
' 2>&1""")
    print("   Config tmpfiles instalada")

    # ===== 7. RESUMEN =====
    print("\n" + "=" * 60)
    print("RESUMEN DE CONFIGURACIONES APLICADAS:")
    out, _ = run_cmd(ssh, """
echo "=== MODPROBE ==="
cat /etc/modprobe.d/usb-ssd-fix.conf 2>/dev/null
echo ""
echo "=== TMPFILES ==="
cat /etc/tmpfiles.d/usb-autosuspend.conf 2>/dev/null
echo ""
echo "=== KERNEL CMDLINE ==="
cat /etc/kernel/cmdline 2>/dev/null || echo "No creado"
echo ""
echo "=== AUTOSUSPEND RUNTIME ==="
cat /sys/module/usbcore/parameters/autosuspend
echo ""
echo "=== UDEV ==="
cat /etc/udev/rules.d/90-ssd-usb.rules 2>/dev/null
echo ""
echo "=== FSTAB ==="
grep " / " /etc/fstab | grep -v "^#"
echo ""
echo "=== TODAS LAS PROTECCIONES ==="
echo pepe1234 | sudo -S crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$"
""")
    print(out)

    ssh.close()
    print("\n✓ CONFIGURACION COMPLETADA")
    print("  REBOOT requerido para aplicar todos los cambios de kernel")

if __name__ == "__main__":
    main()
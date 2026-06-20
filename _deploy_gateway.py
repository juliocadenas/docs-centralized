#!/usr/bin/env python3
"""
Deploy Gateway Config al NAB9
Copia los archivos del gateway al servidor y reinicia el servicio.

Uso:
    python _deploy_gateway.py

Requiere: acceso SSH al NAB9 (pepe@100.105.27.27)
"""
import subprocess
import sys
import os

SERVER = "pepe@100.105.27.27"
REMOTE_PATH = "/mnt/seagate/api/ai-hub-gateway"
FILES_TO_COPY = [
    "ai-hub-gateway/gateway/config.py",
    "ai-hub-gateway/gateway/__init__.py",
]

def run(cmd, check=True):
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"ERROR: {result.stderr}")
        sys.exit(1)
    if result.stdout.strip():
        print(result.stdout.strip())
    return result

def main():
    print("=" * 60)
    print("  🚀 Deploy Gateway Config al NAB9")
    print("=" * 60)

    # 1. Verificar conectividad
    print("\n📡 Verificando conectividad con NAB9...")
    result = subprocess.run(
        f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {SERVER} 'echo OK'",
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        print("❌ No se puede conectar por SSH al NAB9")
        print(f"   Error: {result.stderr}")
        print("\n   Soluciones:")
        print("   1. Verificar que SSH esté habilitado en NAB9")
        print("   2. Verificar Tailscale: ping 100.105.27.27")
        print("   3. Instalar SSH: sudo apt install openssh-server")
        sys.exit(1)
    print("✅ SSH conectado")

    # 2. Copiar archivos
    print("\n📦 Copiando archivos del Gateway...")
    for f in FILES_TO_COPY:
        if os.path.exists(f):
            run(f"scp -o StrictHostKeyChecking=no {f} {SERVER}:{REMOTE_PATH}/gateway/")
            print(f"   ✅ {f}")
        else:
            print(f"   ⚠️  {f} no encontrado, saltando...")

    # 3. Reiniciar Gateway
    print("\n🔄 Reiniciando AI Hub Gateway...")
    run(f"ssh {SERVER} 'sudo systemctl restart ai-hub-gateway'")

    # 4. Verificar
    print("\n✅ Verificando estado...")
    import time
    time.sleep(5)
    result = run(f"ssh {SERVER} 'curl -s http://localhost:9000/v1/status | python3 -m json.tool | head -20'")

    print("\n" + "=" * 60)
    print("  ✅ Deploy completado!")
    print("=" * 60)
    print("\nEl Gateway está actualizado en NAB9.")

if __name__ == "__main__":
    main()
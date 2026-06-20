#!/usr/bin/env python3
"""
Instala Qwen2.5 (7b) y Qwen2.5-coder (7b) en Ollama del servidor NAB9.
Tambien verifica el estado del sistema antes y despues.
"""
import paramiko
import sys
import time

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

MODELS_TO_INSTALL = [
    "qwen2.5:7b",           # Modelo principal de chat (mejor que Llama 3.1 en espanol/razonamiento)
    "qwen2.5-coder:7b",     # Variante optimizada para programacion
]

def run_cmd(ssh, cmd, timeout=600, stream=False):
    """Ejecuta comando SSH y retorna salida. Si stream=True, muestra progreso en tiempo real."""
    print(f"\n{'='*60}")
    print(f"  EJECUTANDO: {cmd}")
    print(f"{'='*60}")
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=stream)
    
    if stream:
        # Modo streaming - filtrar caracteres no ASCII (ollama usa barras Unicode)
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                raw = stdout.channel.recv(4096).decode('ascii', errors='ignore').strip()
                if raw:
                    # Extraer solo el porcentaje si existe
                    if '%' in raw:
                        pct_parts = [p for p in raw.split() if '%' in p]
                        if pct_parts:
                            sys.stdout.write(f"\r  Progreso: {pct_parts[-1]}    ")
                            sys.stdout.flush()
            time.sleep(1.0)
        print()  # newline despues del progreso
    
    exit_code = stdout.channel.recv_exit_status()
    err_output = stderr.read().decode('utf-8', errors='replace').strip()
    out_output = stdout.read().decode('utf-8', errors='replace').strip()
    
    if exit_code != 0 and err_output:
        print(f"  [STDERR]: {err_output[:500]}")
    
    return exit_code, out_output, err_output


def main():
    print("=" * 60)
    print("  INSTALACION DE QWEN2.5 EN AI HUB MADRID (NAB9)")
    print("=" * 60)

    # Conectar SSH
    print(f"\n  Conectando a {USER}@{HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, username=USER, password=PASS, timeout=15)
        print("  [OK] Conexion SSH establecida")
    except Exception as e:
        print(f"  [ERROR] Error conectando: {e}")
        sys.exit(1)

    # 1. Estado ANTES de instalar
    print("\n  ESTADO ANTES DE INSTALAR:")
    print("-" * 40)
    
    _, ollama_list, _ = run_cmd(ssh, "ollama list")
    print(f"Modelos Ollama:\n{ollama_list}")
    
    _, disk, _ = run_cmd(ssh, "df -h /mnt/seagate | tail -1")
    print(f"\nDisco seagate: {disk}")
    
    _, ram, _ = run_cmd(ssh, "free -h | grep Mem")
    print(f"RAM: {ram}")

    # 2. Instalar cada modelo
    for model in MODELS_TO_INSTALL:
        print(f"\n  INSTALANDO: {model}")
        print("-" * 40)
        
        # Verificar si ya esta instalado
        exit_code, out, _ = run_cmd(ssh, f"ollama list | grep -c '{model.split(':')[0]}'")
        if exit_code == 0 and out.strip() != "0":
            print(f"  [SKIP] {model} ya esta instalado, saltando...")
            continue
        
        # Instalar (streaming para ver progreso de descarga)
        exit_code, out, err = run_cmd(
            ssh, 
            f"ollama pull {model}", 
            timeout=1200,  # 20 min max por modelo
            stream=True
        )
        
        if exit_code == 0:
            print(f"  [OK] {model} instalado correctamente")
        else:
            print(f"  [ERROR] Error instalando {model}: {err[:300]}")

    # 3. Estado DESPUES de instalar
    print("\n\n  ESTADO DESPUES DE INSTALAR:")
    print("-" * 40)
    
    _, ollama_list_after, _ = run_cmd(ssh, "ollama list")
    print(f"Modelos Ollama:\n{ollama_list_after}")
    
    _, disk_after, _ = run_cmd(ssh, "df -h /mnt/seagate | tail -1")
    print(f"\nDisco seagate: {disk_after}")

    # 4. Quick test de cada modelo
    print("\n  TEST RAPIDO DE MODELOS:")
    print("-" * 40)
    
    for model in MODELS_TO_INSTALL:
        test_prompt = "Di 'Hola, soy Qwen funcionando correctamente en AI Hub Madrid' en una sola linea. Sin explicaciones extra."
        exit_code, out, _ = run_cmd(
            ssh,
            f'ollama run {model} "{test_prompt}" 2>&1',
            timeout=120
        )
        if exit_code == 0:
            response = out.strip()[:200]
            print(f"\n  {model}:")
            print(f"  Respuesta: {response}")
        else:
            print(f"\n  {model}: [ERROR] Error en test")

    print("\n" + "=" * 60)
    print("  PROCESO COMPLETADO")
    print("=" * 60)
    
    ssh.close()


if __name__ == "__main__":
    main()
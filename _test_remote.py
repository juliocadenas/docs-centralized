"""
Test remoto de modelos en el NAB9.
"""
import paramiko
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "100.105.27.27"
USER = "pepe"
PASS = "pepe1234"

def run_remote(ssh, cmd, timeout=60):
    """Ejecuta comando remoto y devuelve output."""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return exit_code, out, err

def main():
    print("=" * 60)
    print("  TEST REMOTO - AI Hub Gateway + Modelos")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    print("\n[OK] Conectado a NAB9\n")

    # 1. Version del gateway
    print("[1] Version del Gateway:")
    code, out, _ = run_remote(ssh, "curl -s http://localhost:9000/v1/status")
    if out:
        import json
        try:
            d = json.loads(out)
            print(f"    Version: {d.get('gateway_version', '?')}")
            print(f"    Status:  {d.get('status', '?')}")
            print(f"    Uptime:  {d.get('uptime_seconds', 0):.0f}s")
        except:
            print(f"    Raw: {out[:200]}")

    # 2. Test Qwen2.5-VL (texto)
    print("\n[2] Test Qwen2.5-VL (texto):")
    cmd = '''curl -s http://localhost:9000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{"model":"qwen2.5vl:7b","messages":[{"role":"user","content":"Say hello in Spanish, 1 sentence only."}],"stream":false}' '''
    code, out, _ = run_remote(ssh, cmd, timeout=120)
    if out:
        import json
        try:
            d = json.loads(out)
            content = d.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"    Respuesta: {content[:200]}")
        except:
            print(f"    Raw: {out[:300]}")

    # 3. Test Qwen2.5 Coder
    print("\n[3] Test Qwen2.5-Coder:")
    cmd = '''curl -s http://localhost:9000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{"model":"qwen2.5-coder:7b","messages":[{"role":"user","content":"print hello world in Python, 1 line."}],"stream":false}' '''
    code, out, _ = run_remote(ssh, cmd, timeout=120)
    if out:
        import json
        try:
            d = json.loads(out)
            content = d.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"    Respuesta: {content[:200]}")
        except:
            print(f"    Raw: {out[:300]}")

    # 4. Test Embeddings
    print("\n[4] Test Embeddings (nomic-embed-text):")
    cmd = '''curl -s http://localhost:9000/v1/embeddings \
      -H "Content-Type: application/json" \
      -d '{"model":"nomic-embed-text","input":"hello world test"}' '''
    code, out, _ = run_remote(ssh, cmd, timeout=60)
    if out:
        import json
        try:
            d = json.loads(out)
            emb = d.get("data", [{}])[0].get("embedding", [])
            print(f"    Dimensiones: {len(emb)}")
            print(f"    Primeros 3:  {emb[:3]}")
        except:
            print(f"    Raw: {out[:300]}")

    # 5. Test /v1/models
    print("\n[5] Modelos disponibles en /v1/models:")
    code, out, _ = run_remote(ssh, "curl -s http://localhost:9000/v1/models")
    if out:
        import json
        try:
            d = json.loads(out)
            models = d.get("data", [])
            print(f"    Total: {len(models)} modelos")
            for m in models[:10]:
                print(f"      - {m['id']:30s} ({m.get('type','?')})")
            if len(models) > 10:
                print(f"      ... y {len(models)-10} mas")
        except:
            print(f"    Raw: {out[:300]}")

    ssh.close()
    print("\n" + "=" * 60)
    print("  TESTS COMPLETADOS")
    print("=" * 60)

if __name__ == "__main__":
    main()
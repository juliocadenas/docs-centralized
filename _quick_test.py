import paramiko, io, sys, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=10)

def run(cmd, t=15):
    si, so, se = ssh.exec_command(cmd, timeout=t)
    code = so.channel.recv_exit_status()
    return so.read().decode('utf-8','replace').strip()

# 1. Status
out = run('curl -s --max-time 5 http://localhost:9000/v1/status')
if out:
    d = json.loads(out)
    print(f'Gateway v{d["gateway_version"]} - Status: {d["status"]}')
    print(f'Uptime: {d["uptime_seconds"]:.0f}s')

# 2. VRAM
out = run('nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits')
if out:
    parts = [p.strip() for p in out.split(',')]
    print(f'VRAM: {parts[0]}MB / {parts[1]}MB | GPU: {parts[2]}%')

# 3. Chat con qwen2.5:7b
print('\nTesting qwen2.5:7b...')
payload = '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"Di hola en 3 palabras"}],"stream":false}'
out = run(f"curl -s --max-time 30 http://localhost:9000/v1/chat/completions -H 'Content-Type: application/json' -d '{payload}'", 35)
if out:
    d = json.loads(out)
    content = d.get('choices',[{}])[0].get('message',{}).get('content','')
    print(f'  Respuesta: {content[:100]}')

# 4. Embeddings
print('\nTesting nomic-embed-text...')
payload = '{"model":"nomic-embed-text","input":"test embedding"}'
out = run(f"curl -s --max-time 15 http://localhost:9000/v1/embeddings -H 'Content-Type: application/json' -d '{payload}'", 20)
if out:
    d = json.loads(out)
    emb = d.get('data',[{}])[0].get('embedding',[])
    print(f'  Dimensiones: {len(emb)}')

# 5. Modelos instalados en Ollama
print('\nModelos Ollama:')
out = run('curl -s --max-time 5 http://localhost:11434/api/tags')
if out:
    d = json.loads(out)
    for m in d.get('models',[]):
        sz = m.get('size',0)/1024**3
        print(f'  {m["name"]:30s} {sz:.1f}GB')

ssh.close()
print('\nDONE')
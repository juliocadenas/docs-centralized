"""Quick SSH diagnostics for NAB9."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('100.105.27.27', username='pepe', password='pepe1234', timeout=15)

for cmd in ['df -h', 'df -h /var/lib/docker', 'free -h', 'docker system df', 'mount | grep docker']:
    print(f'>>> {cmd}')
    _, o, e = c.exec_command(cmd, timeout=30)
    print(o.read().decode())
    err = e.read().decode()
    if err:
        print('ERR:', err)
    print()

c.close()
print("DONE")
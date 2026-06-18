"""SSH helper - direct or via jump host using paramiko."""
import sys
import paramiko
import io

def run_direct(host, username, password, command, timeout=15):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=username, password=password, timeout=timeout)
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        if out: print(out)
        if err: print(err, file=sys.stderr)
        return stdout.channel.recv_exit_status()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    finally:
        client.close()

def run_via_jump(jump_host, jump_user, jump_pass, 
                 target_host, target_user, target_pass, 
                 command, timeout=15):
    """SSH via jump host."""
    jump = paramiko.SSHClient()
    jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        jump.connect(jump_host, username=jump_user, password=jump_pass, timeout=timeout)
        # Create transport to jump host
        transport = jump.get_transport()
        # Open a channel from jump to target
        dest_addr = (target_host, 22)
        local_addr = ('127.0.0.1', 22)
        channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
        
        # Connect to target via the channel
        target = paramiko.SSHClient()
        target.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target.connect(target_host, username=target_user, password=target_pass, 
                       sock=channel, timeout=timeout)
        
        stdin, stdout, stderr = target.exec_command(command, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        if out: print(out)
        if err: print(err, file=sys.stderr)
        rc = stdout.channel.recv_exit_status()
        target.close()
        return rc
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    finally:
        jump.close()

if __name__ == "__main__":
    # Direct: python ssh_helper.py direct <host> <user> <pass> <command>
    # Jump:   python ssh_helper.py jump <jhost> <juser> <jpass> <thost> <tuser> <tpass> <command>
    mode = sys.argv[1]
    if mode == "direct":
        sys.exit(run_direct(sys.argv[2], sys.argv[3], sys.argv[4], " ".join(sys.argv[5:])))
    elif mode == "jump":
        sys.exit(run_via_jump(
            sys.argv[2], sys.argv[3], sys.argv[4],   # jump host
            sys.argv[5], sys.argv[6], sys.argv[7],   # target host
            " ".join(sys.argv[8:])                     # command
        ))
    else:
        print("Usage: direct|jump ...")
        sys.exit(1)
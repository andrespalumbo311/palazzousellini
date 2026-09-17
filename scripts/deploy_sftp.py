#!/usr/bin/env python3
"""
Deploy static website build artifacts to Hetzner hosting via SFTP.
Resilient against remote directory structures and special characters.
"""

import os
import sys
import paramiko

def main():
    host = os.environ.get('HETZNER_SFTP_HOST')
    user = os.environ.get('HETZNER_SFTP_USER')
    password = os.environ.get('HETZNER_SFTP_PASSWORD')
    port = int(os.environ.get('HETZNER_SFTP_PORT') or 22)
    raw_remote_dir = os.environ.get('HETZNER_REMOTE_DIR', '').strip().strip('/')

    if not host or not user or not password:
        print("ERROR: Missing required SFTP credentials (HOST, USER, PASSWORD).")
        sys.exit(1)

    print(f"Connecting via SFTP to {host}:{port} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    sftp = None
    try:
        ssh.connect(
            host,
            port=port,
            username=user,
            password=password,
            look_for_keys=False,
            allow_agent=False,
            timeout=30
        )
        sftp = ssh.open_sftp()
    except paramiko.ssh_exception.AuthenticationException as e:
        print("Standard password auth rejected, attempting keyboard-interactive fallback...")
        try:
            transport = paramiko.Transport((host, port))
            transport.connect()
            def interactive_handler(title, instructions, prompt_list):
                return [password for _ in prompt_list]
            transport.auth_interactive(user, interactive_handler)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception as fallback_err:
            print(f"Keyboard-interactive fallback failed: {fallback_err}")
            raise e

    cwd = sftp.normalize('.')
    print(f"Connected successfully! Current remote directory: {cwd}")

    try:
        remote_contents = sftp.listdir('.')
        print(f"Existing items in root: {remote_contents}")
    except Exception as e:
        print(f"Could not list current directory: {e}")
        remote_contents = []

    # Determine destination root:
    target_base = ''
    if raw_remote_dir and raw_remote_dir != '.':
        if raw_remote_dir in remote_contents:
            target_base = raw_remote_dir
        else:
            # Check if raw_remote_dir is accessible
            try:
                sftp.stat(raw_remote_dir)
                target_base = raw_remote_dir
            except IOError:
                # If specified folder does not exist, check if public_html exists
                if 'public_html' in remote_contents:
                    target_base = 'public_html'
                else:
                    target_base = raw_remote_dir
    elif 'public_html' in remote_contents:
        target_base = 'public_html'
    else:
        target_base = ''

    print(f"Deploying to remote target base: '{target_base or '.'}'")

    def ensure_remote_dir(path):
        parts = [p for p in path.replace('\\', '/').split('/') if p]
        current = ''
        for part in parts:
            current = f"{current}/{part}" if current else part
            try:
                sftp.stat(current)
            except IOError:
                try:
                    sftp.mkdir(current)
                    print(f"Created remote directory: {current}")
                except Exception:
                    pass

    if target_base:
        ensure_remote_dir(target_base)

    local_root = './public'
    if not os.path.isdir(local_root):
        print(f"ERROR: Build directory {local_root} does not exist.")
        sys.exit(1)

    uploaded = 0
    for root, dirs, files in os.walk(local_root):
        rel_path = os.path.relpath(root, local_root).replace('\\', '/')
        if rel_path == '.':
            remote_path = target_base
        else:
            remote_path = f"{target_base}/{rel_path}" if target_base else rel_path

        if remote_path:
            ensure_remote_dir(remote_path)

        for f in sorted(files):
            local_file = os.path.join(root, f)
            dest_file = f"{remote_path}/{f}" if remote_path else f
            sftp.put(local_file, dest_file)
            uploaded += 1

    try:
        sftp.close()
    except Exception:
        pass
    try:
        ssh.close()
    except Exception:
        pass
    print(f"Deployment complete! Successfully uploaded {uploaded} files.")

if __name__ == '__main__':
    main()

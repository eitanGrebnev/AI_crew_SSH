import os, logging, paramiko
from typing import Tuple
from .. import settings

log = logging.getLogger("ssh")

class SSH:
    def __init__(self):
        self.host = settings.SSH_HOST
        self.user = settings.SSH_USER
        self.pw = settings.SSH_PASS
        self.port = settings.SSH_PORT
        self.key_path = settings.SSH_KEY_PATH

    def _connect(self) -> paramiko.SSHClient:
        log.info(f"[SSH] connect {self.user}@{self.host}:{self.port} key={'yes' if self.key_path else 'no'}")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # try key
        if self.key_path and os.path.exists(self.key_path):
            try:
                pkey = None
                try:
                    pkey = paramiko.Ed25519Key.from_private_key_file(self.key_path)
                except Exception:
                    pkey = paramiko.RSAKey.from_private_key_file(self.key_path)
                client.connect(self.host, port=self.port, username=self.user, pkey=pkey, timeout=20)
                log.info("[SSH] key auth OK")
                return client
            except Exception as e:
                log.warning(f"[SSH] key auth failed: {e}")
                client.close()
        # fallback password
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.host, port=self.port, username=self.user, password=self.pw, timeout=20)
        log.info("[SSH] password auth OK")
        return client

    def run(self, cmd: str) -> Tuple[str, str, int]:
        log.debug(f"[SSH] run: {cmd}")
        c = self._connect()
        try:
            stdin, stdout, stderr = c.exec_command(cmd)
            out = stdout.read().decode(errors='ignore')
            err = stderr.read().decode(errors='ignore')
            code = stdout.channel.recv_exit_status()
            log.debug(f"[SSH] exit={code} out_len={len(out)} err_len={len(err)}")
            return out, err, code
        finally:
            c.close()

    def sftp_backup_and_write(self, remote_path: str, new_content: str) -> str:
        c = self._connect()
        try:
            sftp = c.open_sftp()
            backup_path = remote_path + '.bak'
            try:
                sftp.stat(remote_path)
                with sftp.open(remote_path, 'r') as r, sftp.open(backup_path, 'w') as w:
                    w.write(r.read().decode())
            except FileNotFoundError:
                backup_path = ''
            with sftp.open(remote_path, 'w') as w:
                w.write(new_content)
            sftp.close()
            return backup_path
        finally:
            c.close()

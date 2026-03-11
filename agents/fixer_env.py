import logging
from ..tools.ssh_client import SSH
from .. import settings

log = logging.getLogger("fix.env")
ssh = SSH()

ENV_PATH = f"{settings.STACK_DIR}/.env"

GOOD = {
    "POSTGRES_DB": "authentik",
    "AUTHENTIK_POSTGRES__HOST": "postgres",
    "AUTHENTIK_REDIS__HOST": "redis",
}

class EnvFixer:
    def __init__(self, dry_run: bool = True):
        self.dry = dry_run

    def run(self) -> dict:
        log.info("Checking/patching .env…")
        out, err, code = ssh.run(f"cat {ENV_PATH} || true")
        existing = out.splitlines()
        lines = existing[:]
        changed = False
        for k, v in GOOD.items():
            needle = f"{k}={v}"
            if not any(line.startswith(f"{k}=") for line in existing):
                lines.append(needle)
                changed = True
            else:
                for i, line in enumerate(lines):
                    if line.startswith(f"{k}=") and line.strip() != needle:
                        lines[i] = needle
                        changed = True
        if changed and not self.dry:
            content = "\n".join(lines) + "\n"
            ssh.sftp_backup_and_write(ENV_PATH, content)
            log.info(".env updated")
        else:
            log.info(".env no change (dry_run=%s)", self.dry)
        return {"changed": changed, "path": ENV_PATH}

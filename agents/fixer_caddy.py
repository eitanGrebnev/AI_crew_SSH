import logging
from ..tools.ssh_client import SSH
from .. import settings

log = logging.getLogger("fix.caddy")
ssh = SSH()

CADDY_PATH = f"{settings.STACK_DIR}/Caddyfile"

# NOTE: not an f-string. Curly braces are literal for Caddy syntax.
CADDY_KNOWN_GOOD = """
# Minimal reverse proxy for Authentik
{
    auto_https off
}

auth.hillow.org {
    reverse_proxy authentik:9000
}
"""

class CaddyFixer:
    def __init__(self, dry_run: bool = True):
        self.dry = dry_run

    def run(self) -> dict:
        log.info("Checking/patching Caddyfile…")
        out, err, code = ssh.run(f"cat {CADDY_PATH} || true")
        current = out
        if current.strip() == CADDY_KNOWN_GOOD.strip():
            log.info("Caddyfile already matches known-good")
            return {"changed": False, "path": CADDY_PATH}
        if not self.dry:
            ssh.sftp_backup_and_write(CADDY_PATH, CADDY_KNOWN_GOOD)
            log.info("Caddyfile updated")
        else:
            log.info("Caddyfile differs but dry-run true")
        return {"changed": True, "path": CADDY_PATH}

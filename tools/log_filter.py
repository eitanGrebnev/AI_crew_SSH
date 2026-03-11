from .. import settings
from .ssh_client import SSH
ssh = SSH()

ERROR_WORDS = ["error", "warn", "trace", "csrf", "timeout", "502", "bad gateway"]

def get_first_last(container: str, head_n: int = 100, tail_n: int = 100) -> dict:
    first_out, _, _ = ssh.run(f"docker logs {container} | head -n {head_n}")
    last_out, _, _ = ssh.run(f"docker logs {container} | tail -n {tail_n}")
    return {"first": first_out, "last": last_out}


def get_recent_filtered(container: str, minutes: int | None = None, tail_n: int | None = None) -> list[str]:
    minutes = minutes or settings.LOG_SINCE_MINUTES
    tail_n = tail_n or settings.LOG_TAIL_LINES
    out, _, _ = ssh.run(f"docker logs --since {minutes}m {container} | tail -n {tail_n}")
    lines = out.splitlines()
    filtered = []
    for l in lines:
        lo = l.lower()
        if any(w in lo for w in ERROR_WORDS):
            filtered.append(l)
    return filtered[-tail_n:]
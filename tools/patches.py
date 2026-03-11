from unidiff import PatchSet
import difflib
from .ssh_client import SSH
from .. import settings

ssh = SSH()

def make_unified_diff(old: str, new: str, path: str) -> str:
    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=path + ":old",
        tofile=path + ":new",
    )
    return "".join(diff)


def apply_remote_file(path: str, new_content: str, dry_run: bool = True) -> dict:
    # read current
    out, err, code = ssh.run(f"cat {path}")
    current = out if code == 0 else ""
    diff = make_unified_diff(current, new_content, path)
    result = {"path": path, "dry_run": dry_run, "diff": diff}
    if dry_run:
        return result
    backup = ssh.sftp_backup_and_write(path, new_content)
    result["backup"] = backup
    return result
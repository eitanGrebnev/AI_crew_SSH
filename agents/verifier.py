import logging, requests
from .. import settings

log = logging.getLogger("verifier")

class Verifier:
    def run(self, containers: dict) -> dict:
        # Re-check health via docker
        health = {}
        for svc, cname in containers.items():
            try:
                from ..tools import docker_tools as dt
                health[svc] = dt.get_container_health(cname)
            except Exception:
                health[svc] = "unknown"

        http_ok = False
        try:
            r = requests.get(settings.AUTH_URL, timeout=15, verify=False)
            http_ok = r.status_code < 500
        except Exception as e:
            log.warning("HTTP probe failed: %s", e)
        return {"health": health, "http_ok": http_ok}
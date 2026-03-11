import logging
from ..tools import docker_tools as dt

log = logging.getLogger("diagnoser")

MAX_LOG_CHARS = 2000
WATCH = ("authentik", "worker", "caddy", "redis")

class Diagnoser:
    def __init__(self, mem):
        self.mem = mem

    def minimize(self, snap: dict) -> dict:
        # Only include 'last' chunk and cap aggressively
        small_logs = {}
        for name, v in snap.get("logs", {}).items():
            last = (v.get("last") or "")[-MAX_LOG_CHARS:]
            small_logs[name] = {"last": last}
        return {
            "services": snap.get("services", []),
            "containers": snap.get("containers", {}),
            "health": snap.get("health", {}),
            "logs": small_logs,
        }

    def run(self) -> dict:
        log.info("Collecting snapshot…")
        services = dt.list_services()
        containers, health, logs = {}, {}, {}
        for svc in services:
            cname = dt.find_container_for_service(svc) or svc
            containers[svc] = cname
            health[svc] = dt.get_container_health(cname)
            if svc in WATCH:
                logs[cname] = dt.logs(cname, 100)
        return {"services": services, "containers": containers, "health": health, "logs": logs}

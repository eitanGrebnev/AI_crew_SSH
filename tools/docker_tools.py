import logging, json, re
from .ssh_client import SSH
from .. import settings

log = logging.getLogger("docker")
ssh = SSH()
COMPOSE = f"docker compose -f {settings.COMPOSE_FILE}"

SERVICE_NAME_RE = re.compile(r"^(?P<name>\S+)\s+(?P<image>\S+).*")


def list_services() -> list[str]:
    log.info("Listing compose services…")
    out, err, code = ssh.run(f"{COMPOSE} ps --services")
    if code != 0:
        log.warning(f"list_services failed: {err.strip()}")
    return [s.strip() for s in out.splitlines() if s.strip()]


def find_container_for_service(service: str) -> str | None:
    # Use docker ps names; try common compose name patterns
    out, _, _ = ssh.run("docker ps --format '{{.Names}}'")
    for line in out.splitlines():
        name = line.strip()
        if name.startswith("identity_stack-") and service in name:
            return name
        if name == f"{service}-1":
            return name
        if name.startswith(service + "-"):
            return name
    return None


def get_container_health(container: str) -> str:
    out, _, _ = ssh.run(f"docker inspect --format='{{{{.State.Health.Status}}}}' {container}")
    status = out.strip()
    return status if status else "unknown"


def get_container_status(container: str) -> str:
    out, _, _ = ssh.run(f"docker inspect --format='{{{{.State.Status}}}}' {container}")
    return out.strip() or "unknown"


def logs(service_or_container: str, n: int = 100) -> dict:
    log.info(f"Fetching logs for {service_or_container} (first/last {n})…")
    first_out, _, _ = ssh.run(f"docker logs {service_or_container} 2>&1 | head -n {n}")
    last_out, _, _ = ssh.run(f"docker logs {service_or_container} 2>&1 | tail -n {n}")
    return {"first": first_out, "last": last_out}


def restart_services(services: list[str]) -> None:
    if not services:
        return
    joined = " ".join(services)
    log.info(f"Restarting services: {joined}")
    ssh.run(f"{COMPOSE} up -d --force-recreate {joined}")


def restart_container(container: str) -> None:
    if not container:
        return
    log.info(f"Restarting container: {container}")
    ssh.run(f"docker restart {container}")


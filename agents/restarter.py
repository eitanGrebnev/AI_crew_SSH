import logging
from ..tools import docker_tools as dt

log = logging.getLogger("restarter")

class Restarter:
    def run(self, services: list[str]):
        if not services:
            return
        dt.restart_services(services)

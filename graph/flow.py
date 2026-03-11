# src/graph/flow.py
from __future__ import annotations
import logging
from ..memory.store import Memory
from ..agents.diagnoser import Diagnoser
from ..agents.classifier import Classifier
from ..agents.fixer_env import EnvFixer
from ..agents.fixer_caddy import CaddyFixer
from ..agents.restarter import Restarter
from ..agents.verifier import Verifier
from ..tools import docker_tools as dt
from .. import settings

log = logging.getLogger("flow")

class Flow:
    def __init__(self, llm):
        self.mem = Memory()
        self.llm = llm
        self.diagnoser = Diagnoser(self.mem)
        self.classifier = Classifier(llm)
        self.envfix = EnvFixer(dry_run=settings.DRY_RUN)
        self.caddyfix = CaddyFixer(dry_run=settings.DRY_RUN)
        self.restarter = Restarter()
        self.verifier = Verifier()

    def run(self) -> dict:
        log.info("=== Flow start ===")
        # warmup LLM so first call doesn’t hit a long JIT load
        try:
            self.llm.warmup()
        except Exception as e:
            log.warning(f"warmup failed (continuing): {e}")

        steps = 0
        actions: list[str] = []
        diagnosis_text = ""
        success = False

        while steps < settings.MAX_STEPS:
            steps += 1
            log.info(f"Step {steps}: collecting snapshot…")
            snap = self.diagnoser.run()
            minimal = self.diagnoser.minimize(snap)

            log.info("Classifying issue…")
            diagnosis_text = self.classifier.run(minimal)

            # Basic heuristics
            need_env = (snap["health"].get("authentik") != "healthy") or \
                       (snap["health"].get("worker") != "healthy")
            need_caddy = True  # always enforce sane Caddy

            if need_env:
                log.info("Applying EnvFixer…")
                res = self.envfix.run()
                if res.get("changed"):
                    actions.append(f"env.changed:{res['path']}")

            if need_caddy:
                log.info("Applying CaddyFixer…")
                res = self.caddyfix.run()
                if res.get("changed"):
                    actions.append(f"caddy.changed:{res['path']}")

            log.info("Restarting core services…")
            core = ["authentik", "worker", "caddy"]
            dt.restart_services(core)
            actions.append("restart:authentik,worker,caddy")

            log.info("Verifying…")
            check = self.verifier.run(snap["containers"])
            all_ok = check["http_ok"] and all(
                v == "healthy" for v in check["health"].values() if v
            )
            if all_ok:
                success = True
                break

        self.mem.set_last(diagnosis=diagnosis_text, proposed_fixes=actions, applied=actions)
        self.mem.record_run(diagnosis_text, actions, success)
        self.mem.save()

        return {
            "success": success,
            "diagnosis": diagnosis_text,
            "actions": actions,
        }

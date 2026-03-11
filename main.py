import logging
from .logging_setup import setup_logging
from . import settings
from .memory.store import Memory
from .agents.diagnoser import Diagnoser
from .agents.classifier import Classifier
from .agents.fixer_env import EnvFixer
from .agents.fixer_caddy import CaddyFixer
from .agents.restarter import Restarter
from .agents.verifier import Verifier
from .llm import LMStudioClient, OllamaClient

setup_logging()
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

    def run(self):
        log.info("=== Flow start ===")
        self.llm.warmup()
        steps = 0
        actions: list[str] = []
        diagnosis_text = ""

        while steps < settings.MAX_STEPS:
            steps += 1
            log.info("Step %s: collecting snapshot…", steps)
            snap = self.diagnoser.run()
            minimal = self.diagnoser.minimize(snap)
            log.info("Snapshot minimized, calling classifier.")
            diagnosis_text = self.classifier.run(minimal)
            log.info("Classifier finished.")

            need_env = (snap["health"].get("authentik") != "healthy") or (snap["health"].get("worker") != "healthy")
            need_caddy = True

            if need_env:
                res = self.envfix.run()
                if res.get("changed"):
                    actions.append(f"env.changed:{res['path']}")

            if need_caddy:
                res = self.caddyfix.run()
                if res.get("changed"):
                    actions.append(f"caddy.changed:{res['path']}")

            # Restart core services
            core = ["authentik", "worker", "caddy"]
            self.restarter.run(core)
            actions.append("restart:authentik,worker,caddy")

            # Verify
            check = self.verifier.run(snap["containers"])
            all_ok = check["http_ok"] and all(v == "healthy" for v in check["health"].values() if v)
            if all_ok:
                self.mem.set_last(diagnosis=diagnosis_text, proposed_fixes=actions, applied=actions)
                self.mem.record_run(diagnosis_text, actions, True)
                self.mem.save()
                return {"success": True, "diagnosis": diagnosis_text, "actions": actions, "verify": check}

        self.mem.set_last(diagnosis=diagnosis_text, proposed_fixes=actions, applied=actions)
        self.mem.record_run(diagnosis_text, actions, False)
        self.mem.save()
        return {"success": False, "diagnosis": diagnosis_text, "actions": actions}


def build_llm():
    if settings.LLM_BACKEND.lower() == "ollama":
        return OllamaClient()
    return LMStudioClient(settings.LMSTUDIO_ENDPOINT, settings.LLM_MODEL, settings.LMSTUDIO_API_KEY)

if __name__ == "__main__":
    llm = build_llm()
    flow = Flow(llm)
    result = flow.run()
    log.info("Result: %s", result)

import json, threading, os, logging

log = logging.getLogger("agent.fix_manager")

class FixManager:
    """
    Tracks which fixes have been attempted in a JSON file.
    """
    def __init__(self, path: str = "memory.json"):
        self.path = path
        self.lock = threading.Lock()
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({}, f)
        with open(self.path) as f:
            self.state = json.load(f)

    def should_fix(self, service: str) -> bool:
        return not self.state.get(f"{service}_fix_attempted", False)

    def mark_fixed(self, service: str):
        with self.lock:
            self.state[f"{service}_fix_attempted"] = True
            with open(self.path, "w") as f:
                json.dump(self.state, f, indent=2)
        log.info("FixManager: marked %s as attempted", service)

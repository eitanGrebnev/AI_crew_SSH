import json, os, time


MEM_PATH = os.path.join(os.getcwd(), "agent_memory.json")

class Memory:
    def __init__(self):
        self.state = self._load()

    def _load(self):
        if not os.path.exists(MEM_PATH):
            return {"runs": []}
        try:
            with open(MEM_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"runs": []}

    def save(self):
        with open(MEM_PATH, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def set_last(self, **kwargs):
        self.state.setdefault("last", {}).update(kwargs)

    def record_run(self, diagnosis: str, actions: list[str], success: bool):
        self.state.setdefault("runs", []).append({
            "ts": int(time.time()),
            "diagnosis": diagnosis,
            "actions": actions,
            "success": success,
        })

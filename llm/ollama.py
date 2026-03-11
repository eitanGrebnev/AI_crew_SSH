import requests, logging, json
from .. import settings

log = logging.getLogger("ollama")

class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.timeout = settings.HTTP_TIMEOUT

    def warmup(self):
        try:
            requests.get(f"{self.base_url}/api/tags", timeout=10)
            log.info("[Ollama] warmup ok")
        except Exception as e:
            log.warning("[Ollama] warmup failed: %s", e)

    def chat(self, messages: list[dict]) -> str:
        payload = {"model": self.model, "messages": messages, "stream": False}
        r = requests.post(f"{self.base_url}/v1/chat/completions", data=json.dumps(payload), timeout=self.timeout)
        if not r.ok:
            raise RuntimeError(f"Ollama error {r.status_code}: {r.text}")
        return r.json()["choices"][0]["message"]["content"]

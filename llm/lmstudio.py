import requests, logging, json
from .. import settings

log = logging.getLogger("lmstudio")

class LMStudioClient:
    def __init__(self, base_url: str | None = None, model: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or settings.LMSTUDIO_ENDPOINT).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.api_key = api_key or settings.LMSTUDIO_API_KEY
        self.timeout = settings.HTTP_TIMEOUT
        # target ~4k tokens worth of input; adjust if you increase model context
        self.max_input_chars = 12000

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def list_models(self) -> list[str]:
        try:
            r = requests.get(f"{self.base_url}/v1/models", headers=self._headers(), timeout=30)
            r.raise_for_status()
            data = r.json()
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            log.info("[LMStudio] models ok: %s", models)
            return models
        except Exception as e:
            log.warning("[LMStudio] list_models failed: %s", e)
            return []

    def warmup(self):
        _ = self.list_models()
        log.info("[LMStudio] warmup ok")

    def _shrink_messages(self, messages: list[dict]) -> list[dict]:
        # Keep system messages intact, aggressively shrink user/assistant content from the START, keep the tail.
        total = 0
        out = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if not isinstance(content, str):
                content = str(content)

            if role == "system":
                # keep system as-is
                out.append({"role": role, "content": content})
                total += len(content)
                continue

            remain = self.max_input_chars - total
            if remain <= 0:
                # no more room; keep a tiny tail marker
                out.append({"role": role, "content": "[truncated]"})
                continue

            if len(content) > remain:
                content = content[-remain:]

            out.append({"role": role, "content": content})
            total += len(content)

        return out

    def chat(self, messages: list[dict]) -> str:
        trimmed = self._shrink_messages(messages)
        payload = {
            "model": self.model,
            "messages": trimmed,
            "temperature": 0.2,
            "stream": False,
            "max_tokens": 512
        }
        try:
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers(),
                data=json.dumps(payload),
                timeout=self.timeout,
            )
        except requests.exceptions.ReadTimeout:
            raise RuntimeError("LMStudio chat timeout — model likely still loading; try again.")
        if not resp.ok:
            txt = resp.text
            raise RuntimeError(f"LMStudio error {resp.status_code}: {txt[:2000]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]

import logging
from .. import settings

log = logging.getLogger("classifier")

SYSTEM = """
You are a precise SRE assistant. Read the minimal snapshot and state primary root causes and concrete fixes.
Return a short explanation. Avoid hallucinating. If data is insufficient, say what to collect next.
"""

class Classifier:
    def __init__(self, llm):
        self.llm = llm

    def run(self, minimal: dict) -> str:
        msg = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Snapshot minimal JSON:\n{minimal}"},
        ]
        return self.llm.chat(msg)
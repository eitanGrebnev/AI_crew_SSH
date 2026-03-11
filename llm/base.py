from abc import ABC, abstractmethod
from typing import List, Dict

Message = Dict[str, str]

class LLMClient(ABC):
    @abstractmethod
    def chat(self, messages: List[Message]) -> str:
        ...
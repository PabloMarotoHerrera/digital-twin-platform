from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate_action(self, user_message: str, context: dict) -> dict:
        raise NotImplementedError


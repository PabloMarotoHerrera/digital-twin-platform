from __future__ import annotations

from .base_provider import LLMProvider
from .intent_parser import parse_intent


class MockLLMProvider(LLMProvider):
    def generate_action(self, user_message: str, context: dict) -> dict:
        return parse_intent(user_message)

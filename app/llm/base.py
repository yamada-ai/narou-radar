from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def summarize_weekly_report(self, context: dict) -> str:
        raise NotImplementedError


class NoopLLMProvider(LLMProvider):
    """Placeholder for future LLM-assisted annotation flows."""

    def summarize_weekly_report(self, context: dict) -> str:
        return "LLM integration is disabled in MVP."

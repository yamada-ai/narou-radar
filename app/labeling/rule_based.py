from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import TopicConfig


@dataclass(slots=True)
class LabelDecision:
    theme: str | None
    score: float
    matched_rules: list[str]


class RuleBasedLabeler:
    """Simple deterministic labeler using keyword and regex rules.

    This module is intentionally independent from any LLM provider.
    """

    def __init__(self, topics: list[TopicConfig]) -> None:
        self._topics = topics

    def assign_theme(self, title: str, story: str, keyword: str) -> LabelDecision:
        best_theme: str | None = None
        best_score = 0.0
        best_rules: list[str] = []

        text = f"{title}\n{story}\n{keyword}".lower()
        for topic in self._topics:
            score = 0.0
            rules: list[str] = []
            for token in topic.query_keywords:
                if token.lower() in text:
                    score += 1.0
                    rules.append(f"kw:{token}")
            for pattern in topic.title_patterns:
                if re.search(pattern, title, flags=re.IGNORECASE):
                    score += 1.5
                    rules.append(f"title_re:{pattern}")
            if score > best_score:
                best_theme = topic.slug
                best_score = score
                best_rules = rules

        if best_score <= 0:
            return LabelDecision(theme=None, score=0.0, matched_rules=[])
        return LabelDecision(theme=best_theme, score=best_score, matched_rules=best_rules)

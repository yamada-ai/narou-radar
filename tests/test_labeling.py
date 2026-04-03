from app.config import TopicConfig
from app.labeling.rule_based import RuleBasedLabeler


def test_rule_based_labeling_hits_theme() -> None:
    topics = [TopicConfig(slug="villainess", label="悪役令嬢", query_keywords=["悪役令嬢"], title_patterns=["悪役令嬢"]) ]
    labeler = RuleBasedLabeler(topics)
    decision = labeler.assign_theme("悪役令嬢は復讐する", "story", "")
    assert decision.theme == "villainess"
    assert decision.score > 0

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TopicConfig(BaseModel):
    slug: str
    label: str
    query_keywords: list[str] = Field(default_factory=list)
    title_patterns: list[str] = Field(default_factory=list)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NAROU_", env_file=".env", extra="ignore")

    app_name: str = "Narou Radar MVP"
    db_path: str = "data/narou_radar.duckdb"
    topics_path: str = "config/topics.yaml"

    narou_api_base: str = "https://api.syosetu.com/novelapi/api/"
    narou_rank_api_base: str = "https://api.syosetu.com/rank/rankget/"
    request_timeout_seconds: float = 20.0
    request_retries: int = 3
    request_retry_backoff_seconds: float = 1.5
    request_interval_seconds: float = 0.4

    fetch_per_theme: int = 120


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


def load_topics(path: str | Path | None = None) -> list[TopicConfig]:
    settings = get_settings()
    target = Path(path or settings.topics_path)
    payload = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    topics = payload.get("topics", [])
    return [TopicConfig.model_validate(t) for t in topics]

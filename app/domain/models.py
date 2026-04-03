from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class WorkRecord:
    ncode: str
    title: str
    writer: str
    story: str
    keyword: str
    genre: int | None
    global_point: int
    weekly_point: int
    monthly_point: int
    fav_novel_cnt: int
    review_cnt: int
    all_point: int
    all_hyoka_cnt: int
    novel_type: int | None
    isstop: int | None
    end: int | None
    general_firstup: str | None
    general_lastup: str | None


@dataclass(slots=True)
class ThemeAggregate:
    snapshot_date: date
    theme: str
    works_count: int
    new_works: int
    updated_works: int
    avg_weekly: float
    avg_monthly: float
    max_weekly: int
    total_fav: int
    total_review: int

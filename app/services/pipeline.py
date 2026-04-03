from __future__ import annotations

from datetime import date, datetime, timedelta

from app.collectors.narou_api import NarouApiClient
from app.config import AppSettings, TopicConfig
from app.domain.models import ThemeAggregate
from app.forecasting.naive import MovingAverageForecaster, SeasonalNaiveForecaster
from app.labeling.rule_based import RuleBasedLabeler
from app.scoring.radar import SCORING_VERSION, compute_radar_axes
from app.services.tokenizer import count_tokens
from app.storage.duckdb_repo import DuckDBRepository


class IngestionService:
    def __init__(self, settings: AppSettings, topics: list[TopicConfig]) -> None:
        self.settings = settings
        self.topics = topics

    def run_daily_snapshot(self, target_date: date | None = None) -> int:
        ds = target_date or date.today()
        repo = DuckDBRepository(self.settings.db_path)
        repo.migrate()
        client = NarouApiClient(self.settings)
        labeler = RuleBasedLabeler(self.topics)
        ranking_map, rank_raw = client.fetch_ranking()
        repo.store_raw_response("narou_ranking", "all", rank_raw)

        total = 0
        try:
            for topic in self.topics:
                query = " ".join(topic.query_keywords)
                works, raw = client.fetch_novels(query, self.settings.fetch_per_theme)
                repo.store_raw_response("narou_novelapi", topic.slug, raw)
                repo.upsert_works(works)

                entries: list[dict] = []
                texts: list[str] = []
                for w in works:
                    decision = labeler.assign_theme(w.title, w.story, w.keyword)
                    if decision.theme != topic.slug:
                        continue
                    new_flag = _is_new_work(w.general_firstup, ds)
                    updated = _is_recently_updated(w.general_lastup, ds)
                    entries.append(
                        {
                            "ncode": w.ncode,
                            "ranking": ranking_map.get(w.ncode),
                            "global_point": w.global_point,
                            "weekly_point": w.weekly_point,
                            "monthly_point": w.monthly_point,
                            "fav_novel_cnt": w.fav_novel_cnt,
                            "review_cnt": w.review_cnt,
                            "is_new": new_flag,
                            "updated_recent": updated,
                        }
                    )
                    texts.extend([w.title, w.story])

                repo.insert_snapshots(ds, topic.slug, entries)
                agg = _build_theme_aggregate(ds, topic.slug, entries)
                repo.upsert_theme_aggregate(agg)
                score = compute_radar_axes(agg)
                repo.upsert_radar_score(ds, topic.slug, score, SCORING_VERSION)
                repo.upsert_token_frequencies(ds, topic.slug, "title_story", count_tokens(texts))
                total += len(entries)

                for metric, model in (
                    ("avg_weekly", SeasonalNaiveForecaster()),
                    ("works_count", MovingAverageForecaster()),
                ):
                    history = repo.get_aggregate_history(topic.slug, metric)
                    forecast = model.predict(history, horizon=7)
                    repo.store_forecast(topic.slug, metric, forecast, model.name)
        finally:
            client.close()
            repo.close()

        return total


def _build_theme_aggregate(snapshot_date: date, theme: str, entries: list[dict]) -> ThemeAggregate:
    if not entries:
        return ThemeAggregate(snapshot_date, theme, 0, 0, 0, 0.0, 0.0, 0, 0, 0)
    works_count = len(entries)
    new_works = sum(e["is_new"] for e in entries)
    updated_works = sum(e["updated_recent"] for e in entries)
    weekly = [e["weekly_point"] for e in entries]
    monthly = [e["monthly_point"] for e in entries]
    return ThemeAggregate(
        snapshot_date=snapshot_date,
        theme=theme,
        works_count=works_count,
        new_works=new_works,
        updated_works=updated_works,
        avg_weekly=sum(weekly) / max(len(weekly), 1),
        avg_monthly=sum(monthly) / max(len(monthly), 1),
        max_weekly=max(weekly),
        total_fav=sum(e["fav_novel_cnt"] for e in entries),
        total_review=sum(e["review_cnt"] for e in entries),
    )


def _is_new_work(firstup: str | None, ds: date) -> int:
    if not firstup:
        return 0
    try:
        d = datetime.strptime(firstup[:10], "%Y-%m-%d").date()
    except ValueError:
        return 0
    return int(d >= ds - timedelta(days=7))


def _is_recently_updated(lastup: str | None, ds: date) -> int:
    if not lastup:
        return 0
    try:
        d = datetime.strptime(lastup[:10], "%Y-%m-%d").date()
    except ValueError:
        return 0
    return int(d >= ds - timedelta(days=3))


class MetricsRecomputeService:
    """Recompute aggregates/radar/forecast from existing snapshots without API calls."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def recompute_metrics_from_snapshots(self, target_date: date | None = None) -> int:
        ds = target_date or date.today()
        repo = DuckDBRepository(self.settings.db_path)
        repo.migrate()
        updated = 0
        try:
            for theme in repo.list_snapshot_themes(ds):
                entries = repo.get_snapshot_entries(ds, theme)
                agg = _build_theme_aggregate(ds, theme, entries)
                repo.upsert_theme_aggregate(agg)
                score = compute_radar_axes(agg)
                repo.upsert_radar_score(ds, theme, score, SCORING_VERSION)
                for metric, model in (
                    ("avg_weekly", SeasonalNaiveForecaster()),
                    ("works_count", MovingAverageForecaster()),
                ):
                    history = repo.get_aggregate_history(theme, metric)
                    forecast = model.predict(history, horizon=7)
                    repo.store_forecast(theme, metric, forecast, model.name)
                updated += 1
        finally:
            repo.close()
        return updated

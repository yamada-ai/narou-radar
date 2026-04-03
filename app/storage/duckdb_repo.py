from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import duckdb

from app.domain.models import ThemeAggregate, WorkRecord


class DuckDBRepository:
    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(db_path)

    def close(self) -> None:
        self.conn.close()

    def migrate(self) -> None:
        self.conn.execute(
            """
            create table if not exists raw_api_responses (
              id bigint,
              fetched_at timestamp,
              source varchar,
              theme varchar,
              payload json
            );

            create table if not exists works (
              ncode varchar primary key,
              title varchar,
              writer varchar,
              story varchar,
              keyword varchar,
              genre integer,
              global_point integer,
              weekly_point integer,
              monthly_point integer,
              fav_novel_cnt integer,
              review_cnt integer,
              all_point integer,
              all_hyoka_cnt integer,
              novel_type integer,
              isstop integer,
              end_flag integer,
              general_firstup varchar,
              general_lastup varchar,
              updated_at timestamp
            );

            create table if not exists snapshots (
              snapshot_date date,
              theme varchar,
              ncode varchar,
              ranking integer,
              global_point integer,
              weekly_point integer,
              monthly_point integer,
              fav_novel_cnt integer,
              review_cnt integer,
              is_new integer,
              updated_recent integer,
              primary key (snapshot_date, theme, ncode)
            );

            create table if not exists daily_theme_aggregates (
              snapshot_date date,
              theme varchar,
              works_count integer,
              new_works integer,
              updated_works integer,
              avg_weekly double,
              avg_monthly double,
              max_weekly integer,
              total_fav integer,
              total_review integer,
              primary key (snapshot_date, theme)
            );

            create table if not exists radar_scores (
              snapshot_date date,
              theme varchar,
              demand_heat double,
              supply_pressure double,
              entry_opportunity double,
              sustainability double,
              calc_version varchar,
              primary key (snapshot_date, theme)
            );

            create table if not exists token_frequencies (
              snapshot_date date,
              theme varchar,
              source varchar,
              token varchar,
              token_count integer,
              primary key (snapshot_date, theme, source, token)
            );

            create table if not exists forecast_results (
              theme varchar,
              metric varchar,
              ds date,
              yhat double,
              model varchar,
              created_at timestamp
            );
            """
        )

    def store_raw_response(self, source: str, theme: str, payload: str) -> None:
        self.conn.execute(
            "insert into raw_api_responses values (?, ?, ?, ?, ?)",
            [int(datetime.now(timezone.utc).timestamp()*1000), datetime.now(timezone.utc), source, theme, payload],
        )

    def upsert_works(self, works: list[WorkRecord]) -> None:
        for w in works:
            self.conn.execute(
                """
                insert into works values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict (ncode) do update set
                  title=excluded.title,
                  writer=excluded.writer,
                  story=excluded.story,
                  keyword=excluded.keyword,
                  genre=excluded.genre,
                  global_point=excluded.global_point,
                  weekly_point=excluded.weekly_point,
                  monthly_point=excluded.monthly_point,
                  fav_novel_cnt=excluded.fav_novel_cnt,
                  review_cnt=excluded.review_cnt,
                  all_point=excluded.all_point,
                  all_hyoka_cnt=excluded.all_hyoka_cnt,
                  novel_type=excluded.novel_type,
                  isstop=excluded.isstop,
                  end_flag=excluded.end_flag,
                  general_firstup=excluded.general_firstup,
                  general_lastup=excluded.general_lastup,
                  updated_at=excluded.updated_at
                """,
                [
                    w.ncode,
                    w.title,
                    w.writer,
                    w.story,
                    w.keyword,
                    w.genre,
                    w.global_point,
                    w.weekly_point,
                    w.monthly_point,
                    w.fav_novel_cnt,
                    w.review_cnt,
                    w.all_point,
                    w.all_hyoka_cnt,
                    w.novel_type,
                    w.isstop,
                    w.end,
                    w.general_firstup,
                    w.general_lastup,
                    datetime.now(timezone.utc),
                ],
            )

    def insert_snapshots(self, snapshot_date: date, theme: str, entries: list[dict]) -> None:
        for e in entries:
            self.conn.execute(
                """
                insert into snapshots values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict do update set
                  ranking=excluded.ranking,
                  global_point=excluded.global_point,
                  weekly_point=excluded.weekly_point,
                  monthly_point=excluded.monthly_point,
                  fav_novel_cnt=excluded.fav_novel_cnt,
                  review_cnt=excluded.review_cnt,
                  is_new=excluded.is_new,
                  updated_recent=excluded.updated_recent
                """,
                [
                    snapshot_date,
                    theme,
                    e["ncode"],
                    e.get("ranking"),
                    e["global_point"],
                    e["weekly_point"],
                    e["monthly_point"],
                    e["fav_novel_cnt"],
                    e["review_cnt"],
                    int(e["is_new"]),
                    int(e["updated_recent"]),
                ],
            )

    def upsert_theme_aggregate(self, agg: ThemeAggregate) -> None:
        self.conn.execute(
            """
            insert into daily_theme_aggregates values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict do update set
              works_count=excluded.works_count,
              new_works=excluded.new_works,
              updated_works=excluded.updated_works,
              avg_weekly=excluded.avg_weekly,
              avg_monthly=excluded.avg_monthly,
              max_weekly=excluded.max_weekly,
              total_fav=excluded.total_fav,
              total_review=excluded.total_review
            """,
            [
                agg.snapshot_date,
                agg.theme,
                agg.works_count,
                agg.new_works,
                agg.updated_works,
                agg.avg_weekly,
                agg.avg_monthly,
                agg.max_weekly,
                agg.total_fav,
                agg.total_review,
            ],
        )

    def upsert_radar_score(self, snapshot_date: date, theme: str, score: dict[str, float], version: str) -> None:
        self.conn.execute(
            """
            insert into radar_scores values (?, ?, ?, ?, ?, ?, ?)
            on conflict do update set
              demand_heat=excluded.demand_heat,
              supply_pressure=excluded.supply_pressure,
              entry_opportunity=excluded.entry_opportunity,
              sustainability=excluded.sustainability,
              calc_version=excluded.calc_version
            """,
            [
                snapshot_date,
                theme,
                score["demand_heat"],
                score["supply_pressure"],
                score["entry_opportunity"],
                score["sustainability"],
                version,
            ],
        )

    def upsert_token_frequencies(self, snapshot_date: date, theme: str, source: str, tokens: dict[str, int]) -> None:
        for token, count in tokens.items():
            self.conn.execute(
                """
                insert into token_frequencies values (?, ?, ?, ?, ?)
                on conflict do update set token_count=excluded.token_count
                """,
                [snapshot_date, theme, source, token, count],
            )

    def list_latest_themes(self) -> list[dict]:
        return self.conn.execute(
            """
            with latest as (
              select max(snapshot_date) as ds from radar_scores
            )
            select r.theme, r.snapshot_date, r.demand_heat, r.supply_pressure, r.entry_opportunity, r.sustainability,
                   a.works_count, a.avg_weekly
            from radar_scores r
            join latest l on r.snapshot_date = l.ds
            left join daily_theme_aggregates a on a.snapshot_date = r.snapshot_date and a.theme = r.theme
            order by r.theme
            """
        ).fetchdf().to_dict("records")

    def get_theme_detail(self, theme: str, days: int = 30) -> dict:
        latest = self.conn.execute(
            "select * from radar_scores where theme=? order by snapshot_date desc limit 1", [theme]
        ).fetchone()
        series = self.conn.execute(
            """
            select a.snapshot_date, a.works_count, a.avg_weekly, a.new_works, a.updated_works,
                   r.demand_heat, r.supply_pressure, r.entry_opportunity, r.sustainability
            from daily_theme_aggregates a
            join radar_scores r on a.snapshot_date=r.snapshot_date and a.theme=r.theme
            where a.theme=? and a.snapshot_date >= ?
            order by a.snapshot_date
            """,
            [theme, date.today() - timedelta(days=days)],
        ).fetchdf().to_dict("records")
        return {"latest": latest, "series": series}

    def get_aggregate_history(self, theme: str, metric: str, days: int = 60) -> list[tuple[date, float]]:
        rows = self.conn.execute(
            f"""
            select snapshot_date, {metric}
            from daily_theme_aggregates
            where theme=? and snapshot_date >= ?
            order by snapshot_date
            """,
            [theme, date.today() - timedelta(days=days)],
        ).fetchall()
        return rows

    def store_forecast(self, theme: str, metric: str, preds: list[tuple[date, float]], model: str) -> None:
        now = datetime.now(timezone.utc)
        for ds, yhat in preds:
            self.conn.execute(
                "insert into forecast_results values (?, ?, ?, ?, ?, ?)",
                [theme, metric, ds, yhat, model, now],
            )

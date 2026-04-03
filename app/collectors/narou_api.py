from __future__ import annotations

import json
import time
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from app.config import AppSettings
from app.domain.models import WorkRecord


class NarouApiClient:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._client = httpx.Client(timeout=settings.request_timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def _request_json(self, url: str, params: dict[str, Any]) -> Any:
        last_error: Exception | None = None
        for i in range(self.settings.request_retries):
            try:
                res = self._client.get(url, params=params)
                res.raise_for_status()
                time.sleep(self.settings.request_interval_seconds)
                return res.json()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(self.settings.request_retry_backoff_seconds * (i + 1))
        raise RuntimeError(f"API request failed after retries: {last_error}")

    def fetch_novels(self, keyword_query: str, limit: int) -> tuple[list[WorkRecord], str]:
        fields = "ncode,title,writer,story,keyword,genre,global_point,weekly_point,monthly_point,fav_novel_cnt,review_cnt,all_point,all_hyoka_cnt,novel_type,isstop,end,general_firstup,general_lastup"
        params = {
            "out": "json",
            "of": f"t-{fields}",
            "word": keyword_query,
            "lim": limit,
            "order": "weeklypoint",
        }
        payload = self._request_json(self.settings.narou_api_base, params=params)
        raw_text = json.dumps(payload, ensure_ascii=False)
        rows = payload[1:] if isinstance(payload, list) and payload else []
        works = [self._parse_work(r) for r in rows if isinstance(r, dict)]
        return works, raw_text

    def fetch_ranking(self) -> tuple[dict[str, int], str]:
        jst = timezone(timedelta(hours=9))
        now = datetime.now(jst)
        params = {
            "out": "json",
            "rtype": "all",
            "date": now.strftime("%Y%m%d"),
        }
        try:
            payload = self._request_json(self.settings.narou_rank_api_base, params=params)
        except Exception:
            return {}, "[]"
        raw_text = json.dumps(payload, ensure_ascii=False)
        rank_map: dict[str, int] = {}
        if isinstance(payload, list):
            for i, row in enumerate(payload):
                if not isinstance(row, dict):
                    continue
                ncode = row.get("ncode")
                if isinstance(ncode, str):
                    rank_map[ncode.upper()] = i + 1
        return rank_map, raw_text

    @staticmethod
    def _parse_work(row: dict[str, Any]) -> WorkRecord:
        return WorkRecord(
            ncode=str(row.get("ncode", "")).upper(),
            title=str(row.get("title", "")),
            writer=str(row.get("writer", "")),
            story=str(row.get("story", "")),
            keyword=str(row.get("keyword", "")),
            genre=_as_int(row.get("genre")),
            global_point=_as_int(row.get("global_point"), 0),
            weekly_point=_as_int(row.get("weekly_point"), 0),
            monthly_point=_as_int(row.get("monthly_point"), 0),
            fav_novel_cnt=_as_int(row.get("fav_novel_cnt"), 0),
            review_cnt=_as_int(row.get("review_cnt"), 0),
            all_point=_as_int(row.get("all_point"), 0),
            all_hyoka_cnt=_as_int(row.get("all_hyoka_cnt"), 0),
            novel_type=_as_int(row.get("novel_type")),
            isstop=_as_int(row.get("isstop")),
            end=_as_int(row.get("end")),
            general_firstup=str(row.get("general_firstup")) if row.get("general_firstup") else None,
            general_lastup=str(row.get("general_lastup")) if row.get("general_lastup") else None,
        )


def _as_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

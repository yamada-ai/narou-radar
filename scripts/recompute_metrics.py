from __future__ import annotations

from datetime import date

from app.config import get_settings, load_topics
from app.services.pipeline import IngestionService


def main() -> None:
    service = IngestionService(get_settings(), load_topics())
    rows = service.run_daily_snapshot(target_date=date.today())
    print(f"recomputed rows: {rows}")


if __name__ == "__main__":
    main()

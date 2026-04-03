from __future__ import annotations

import argparse

from app.config import get_settings, load_topics
from app.services.pipeline import IngestionService


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Narou data and build daily snapshot")
    parser.add_argument("--theme", default="all", help="Topic slug or all")
    args = parser.parse_args()

    settings = get_settings()
    topics = load_topics()
    if args.theme != "all":
        topics = [t for t in topics if t.slug == args.theme]
    service = IngestionService(settings, topics)
    rows = service.run_daily_snapshot()
    print(f"ingested_rows={rows}")


if __name__ == "__main__":
    main()

from __future__ import annotations

from datetime import date

from app.config import get_settings
from app.services.pipeline import MetricsRecomputeService


def main() -> None:
    service = MetricsRecomputeService(get_settings())
    updated_themes = service.recompute_metrics_from_snapshots(target_date=date.today())
    print(f"recomputed themes from snapshots: {updated_themes}")


if __name__ == "__main__":
    main()

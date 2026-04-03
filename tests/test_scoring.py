from datetime import date

from app.domain.models import ThemeAggregate
from app.scoring.radar import compute_radar_axes


def test_compute_radar_axes_range() -> None:
    agg = ThemeAggregate(
        snapshot_date=date(2026, 4, 3),
        theme="exile",
        works_count=80,
        new_works=12,
        updated_works=30,
        avg_weekly=120.0,
        avg_monthly=400.0,
        max_weekly=1000,
        total_fav=2500,
        total_review=90,
    )
    score = compute_radar_axes(agg)
    assert set(score.keys()) == {"demand_heat", "supply_pressure", "entry_opportunity", "sustainability"}
    assert all(0 <= v <= 100 for v in score.values())

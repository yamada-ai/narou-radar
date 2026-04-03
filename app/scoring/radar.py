from __future__ import annotations

from math import exp

from app.domain.models import ThemeAggregate

SCORING_VERSION = "v0.1-mvp"


def _sigmoid_scaled(x: float, k: float = 0.02) -> float:
    return 100.0 / (1.0 + exp(-k * x))


def compute_radar_axes(agg: ThemeAggregate) -> dict[str, float]:
    """Compute four radar axes (0-100) from deterministic formulas.

    Formulas are intentionally explicit and tunable for fast iteration.
    """

    demand_signal = (
        agg.avg_weekly * 0.55
        + agg.avg_monthly * 0.25
        + agg.total_fav * 0.015
        + agg.total_review * 0.08
    )
    demand_heat = _sigmoid_scaled(demand_signal)

    supply_signal = agg.works_count * 1.2 + agg.new_works * 2.0 + agg.updated_works * 1.0
    supply_pressure = _sigmoid_scaled(supply_signal, k=0.06)

    # Higher demand + lower supply => higher opportunity
    balance = demand_heat - supply_pressure + agg.new_works * 0.5
    entry_opportunity = max(0.0, min(100.0, 50.0 + balance * 0.6))

    weekly_monthly_ratio = agg.avg_weekly / max(agg.avg_monthly, 1.0)
    continuity = agg.updated_works / max(agg.works_count, 1)
    sustainability = max(0.0, min(100.0, 40.0 * weekly_monthly_ratio + 60.0 * continuity))

    return {
        "demand_heat": round(demand_heat, 2),
        "supply_pressure": round(supply_pressure, 2),
        "entry_opportunity": round(entry_opportunity, 2),
        "sustainability": round(sustainability, 2),
    }

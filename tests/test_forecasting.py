from datetime import date

from app.forecasting.naive import MovingAverageForecaster, SeasonalNaiveForecaster


def test_forecasters_return_horizon_points() -> None:
    series = [(date(2026, 4, d), float(d)) for d in range(1, 8)]
    s = SeasonalNaiveForecaster().predict(series, horizon=5)
    m = MovingAverageForecaster().predict(series, horizon=5)
    assert len(s) == 5
    assert len(m) == 5

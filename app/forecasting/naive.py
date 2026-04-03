from __future__ import annotations

from datetime import timedelta

from app.forecasting.base import Forecaster


class SeasonalNaiveForecaster(Forecaster):
    name = "seasonal_naive"

    def __init__(self, season_length: int = 7) -> None:
        self.season_length = season_length

    def predict(self, series: list[tuple], horizon: int) -> list[tuple]:
        if not series:
            return []
        tail = series[-self.season_length :] if len(series) >= self.season_length else series
        preds = []
        last_date = series[-1][0]
        for i in range(horizon):
            y = float(tail[i % len(tail)][1])
            preds.append((last_date + timedelta(days=i + 1), y))
        return preds


class MovingAverageForecaster(Forecaster):
    name = "moving_average"

    def __init__(self, window: int = 7) -> None:
        self.window = window

    def predict(self, series: list[tuple], horizon: int) -> list[tuple]:
        if not series:
            return []
        values = [float(x[1]) for x in series[-self.window :]]
        mean = sum(values) / len(values)
        last_date = series[-1][0]
        return [(last_date + timedelta(days=i + 1), mean) for i in range(horizon)]

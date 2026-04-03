from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date


class Forecaster(ABC):
    name: str

    @abstractmethod
    def predict(self, series: list[tuple[date, float]], horizon: int) -> list[tuple[date, float]]:
        raise NotImplementedError

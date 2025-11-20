from __future__ import annotations

from typing import Iterable, Tuple
import numpy as np


def normalize_series(closes: Iterable[float]) -> Tuple[np.ndarray, float, float]:
    """Normalize close prices to zero mean / unit std to stabilize inference."""
    series = np.asarray(list(closes), dtype=np.float32)
    if series.size == 0:
        raise ValueError("'closes' must contain at least one price")
    mean = float(series.mean())
    std = float(series.std()) or 1.0
    normalized = (series - mean) / std
    return normalized, mean, std


def reshape_for_lstm(series: np.ndarray) -> np.ndarray:
    if series.ndim != 1:
        raise ValueError("Series must be 1-D before reshaping")
    return series.reshape(1, series.shape[0], 1)

from __future__ import annotations

from math import sqrt
from typing import Dict, Iterable, List, Tuple

import numpy as np  # type: ignore[import]
from scipy.stats import wilcoxon  # type: ignore[import]


def cliffs_delta(a: Iterable[float], b: Iterable[float]) -> float:
    """Compute Cliff's delta effect size."""
    a_list = list(a)
    b_list = list(b)
    total = len(a_list) * len(b_list)
    if total == 0:
        return 0.0
    greater = 0
    smaller = 0
    for x in a_list:
        for y in b_list:
            if x > y:
                greater += 1
            elif x < y:
                smaller += 1
    return (greater - smaller) / total


def bootstrap_ci(values: Iterable[float], *, n_resamples: int = 1000, alpha: float = 0.05) -> Tuple[float, float]:
    samples = np.array(list(values))
    if len(samples) == 0:
        return (0.0, 0.0)
    boots = []
    for _ in range(n_resamples):
        sample = np.random.choice(samples, size=len(samples), replace=True)
        boots.append(np.mean(sample))
    lower = np.percentile(boots, alpha / 2 * 100)
    upper = np.percentile(boots, (1 - alpha / 2) * 100)
    return float(lower), float(upper)


def wilcoxon_test(a: Iterable[float], b: Iterable[float]) -> Dict[str, float]:
    a_list = list(a)
    b_list = list(b)
    if len(a_list) != len(b_list):
        raise ValueError("Wilcoxon test requires paired samples of equal length.")
    if not a_list:
        return {"statistic": 0.0, "p_value": 1.0}
    stat, p_value = wilcoxon(a_list, b_list, zero_method="wilcox", correction=False)
    return {"statistic": float(stat), "p_value": float(p_value)}



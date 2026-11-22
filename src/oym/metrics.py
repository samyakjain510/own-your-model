"""Scoring statistics with honest uncertainty.

Every rate the kit reports comes with a 95% interval, because on a few hundred
test items the difference between 0.81 and 0.84 is often noise.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

Z95 = 1.959963984540054


@dataclass
class Rate:
    k: int
    n: int
    lo: float
    hi: float

    @property
    def p(self) -> float:
        return self.k / self.n if self.n else float("nan")

    def __str__(self) -> str:
        return f"{self.p:.3f} [{self.lo:.3f}, {self.hi:.3f}] (n={self.n})"


def wilson(k: int, n: int, z: float = Z95) -> Rate:
    """Wilson score interval for a proportion k/n.

    Behaves better than the textbook p ± z*sqrt(p(1-p)/n) when n is small or p
    is near 0 or 1.
    """
    if n == 0:
        return Rate(k, n, float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return Rate(k, n, max(0.0, center - half), min(1.0, center + half))


def confusion(pred: list[bool], truth: list[bool]) -> dict[str, int]:
    tp = sum(p and t for p, t in zip(pred, truth))
    tn = sum((not p) and (not t) for p, t in zip(pred, truth))
    fp = sum(p and (not t) for p, t in zip(pred, truth))
    fn = sum((not p) and t for p, t in zip(pred, truth))
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def tpr_tnr(pred: list[bool], truth: list[bool]) -> tuple[Rate, Rate]:
    """True positive rate (catches real problems) and true negative rate (leaves good items alone)."""
    c = confusion(pred, truth)
    return wilson(c["tp"], c["tp"] + c["fn"]), wilson(c["tn"], c["tn"] + c["fp"])


def cohen_kappa(a: list, b: list) -> float:
    """Agreement between two raters beyond what chance would give. 1 = perfect, 0 = chance."""
    n = len(a)
    if n == 0:
        return float("nan")
    labels = set(a) | set(b)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(lab) / n) * (b.count(lab) / n) for lab in labels)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def bootstrap_ci(a: list, b: list, stat=cohen_kappa, iters: int = 2000, seed: int = 0) -> tuple[float, float]:
    """Percentile bootstrap interval for a paired statistic such as kappa."""
    rng = random.Random(seed)
    n = len(a)
    vals = []
    for _ in range(iters):
        idx = [rng.randrange(n) for _ in range(n)]
        v = stat([a[i] for i in idx], [b[i] for i in idx])
        if not math.isnan(v):
            vals.append(v)
    vals.sort()
    if not vals:
        return float("nan"), float("nan")
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def paired_diff_ci(correct_a: list[bool], correct_b: list[bool], iters: int = 2000, seed: int = 0):
    """Bootstrap interval for accuracy(A) - accuracy(B) on the same test items."""
    rng = random.Random(seed)
    n = len(correct_a)
    diffs = []
    for _ in range(iters):
        idx = [rng.randrange(n) for _ in range(n)]
        diffs.append(sum(correct_a[i] for i in idx) / n - sum(correct_b[i] for i in idx) / n)
    diffs.sort()
    point = sum(correct_a) / n - sum(correct_b) / n
    return point, diffs[int(0.025 * iters)], diffs[int(0.975 * iters) - 1]

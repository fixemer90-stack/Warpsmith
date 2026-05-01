"""NumPy-backed dice pool and Monte Carlo helpers."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass
class SimulationStats:
    mean: float
    median: float
    std: float
    min_val: int
    max_val: int
    percentiles: dict[int, float]
    pmf: list[tuple[int, float]]
    kill_probability: float


class DicePool:
    """D6 pool for Monte Carlo combat simulations."""

    def __init__(self, seed: int | None = None):
        self.rng = np.random.default_rng(seed)

    def d6(self, count: int = 1) -> np.ndarray:
        """Roll count D6 and return values in the inclusive range [1, 6]."""
        return self.rng.integers(1, 7, size=count)

    def d3(self, count: int = 1) -> np.ndarray:
        """Roll count D3 and return values in the inclusive range [1, 3]."""
        return self.rng.integers(1, 4, size=count)

    def successes(self, rolls: np.ndarray, target: int) -> int:
        """Count how many rolls meet or exceed the target value."""
        return int(np.sum(rolls >= target))

    def roll_and_count(self, count: int, target: int) -> int:
        """Roll count D6 and count how many are successes."""
        return self.successes(self.d6(count), target)

    def simulate(
        self,
        func: Callable[[np.random.Generator], int],
        n: int = 10000,
    ) -> np.ndarray:
        """Run func n times and return the result array."""
        return np.array([func(self.rng) for _ in range(n)], dtype=int)

    def simulate_batched(
        self,
        func: Callable[[np.random.Generator], int],
        n: int = 10000,
        batch_size: int = 1000,
    ) -> np.ndarray:
        """Run func n times in batches and return the result array."""
        results: list[int] = []
        for batch_start in range(0, n, batch_size):
            batch_n = min(batch_size, n - batch_start)
            for _ in range(batch_n):
                results.append(func(self.rng))
        return np.array(results, dtype=int)


def compute_stats(results: np.ndarray, target_wounds: int = 1) -> SimulationStats:
    """Compute distribution statistics for Monte Carlo result arrays."""
    unique, counts = np.unique(results, return_counts=True)
    probabilities = counts / len(results)

    return SimulationStats(
        mean=float(np.mean(results)),
        median=float(np.median(results)),
        std=float(np.std(results)),
        min_val=int(np.min(results)),
        max_val=int(np.max(results)),
        percentiles={p: float(np.percentile(results, p)) for p in [5, 25, 50, 75, 95]},
        pmf=[(int(damage), float(probability)) for damage, probability in zip(unique, probabilities, strict=False)],
        kill_probability=float(np.mean(results >= target_wounds)),
    )

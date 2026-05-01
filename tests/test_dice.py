import numpy as np

from backend.engine.dice import DicePool, compute_stats


def test_d6_range() -> None:
    pool = DicePool(seed=42)
    rolls = pool.d6(1000)

    assert np.all(rolls >= 1)
    assert np.all(rolls <= 6)
    assert len(rolls) == 1000


def test_d3_range() -> None:
    pool = DicePool(seed=42)
    rolls = pool.d3(1000)

    assert np.all(rolls >= 1)
    assert np.all(rolls <= 3)
    assert len(rolls) == 1000


def test_successes() -> None:
    pool = DicePool(seed=42)
    rolls = np.array([3, 4, 5, 6])

    assert pool.successes(rolls, 4) == 3


def test_roll_and_count() -> None:
    pool = DicePool(seed=42)
    successes = pool.roll_and_count(100, 4)

    assert 0 <= successes <= 100


def test_seed_reproducibility() -> None:
    a = DicePool(seed=42).d6(10)
    b = DicePool(seed=42).d6(10)

    assert np.array_equal(a, b)


def test_simulate() -> None:
    pool = DicePool(seed=42)

    def always_one(_rng: np.random.Generator) -> int:
        return 1

    results = pool.simulate(always_one, n=100)

    assert isinstance(results, np.ndarray)
    assert np.all(results == 1)
    assert len(results) == 100


def test_simulate_batched_same_as_regular() -> None:
    def one_damage(rng: np.random.Generator) -> int:
        return int(rng.integers(1, 3))

    regular = DicePool(seed=42).simulate(one_damage, n=1000)
    batched = DicePool(seed=42).simulate_batched(one_damage, n=1000, batch_size=100)

    np.testing.assert_array_equal(regular, batched)


def test_compute_stats() -> None:
    results = np.array([0, 0, 0, 1, 1, 2])
    stats = compute_stats(results, target_wounds=2)

    assert abs(stats.mean - 0.67) < 0.01
    assert stats.pmf[0] == (0, 0.5)
    assert abs(stats.kill_probability - (1 / 6)) < 0.01
    assert stats.min_val == 0
    assert stats.max_val == 2

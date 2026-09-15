import numpy as np
import pandas as pd

from market_anchor_1x2_v1_robustness import (
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    FROZEN_FEATURE_VARIANT,
    FROZEN_LAMBDA,
    TARGET_LEAGUE,
    TEST_SEASON,
    TRAIN_SEASONS,
    VALIDATION_SEASON,
    frozen_final_split,
    paired_bootstrap,
    per_match_deltas,
)


def test_frozen_robustness_contract_cannot_search_candidate():
    assert TARGET_LEAGUE == "SERIE_A"
    assert FROZEN_FEATURE_VARIANT == "ALL_FOOTBALL"
    assert FROZEN_LAMBDA == 1.0
    assert BOOTSTRAP_SEED == 20260915
    assert BOOTSTRAP_DRAWS == 20000


def test_per_match_deltas_zero_for_market_identity():
    y = np.array([0, 1, 2])
    market = np.array([[0.5, 0.3, 0.2], [0.2, 0.5, 0.3], [0.2, 0.3, 0.5]])
    db, dl = per_match_deltas(y, market.copy(), market)
    assert np.array_equal(db, np.zeros(3))
    assert np.array_equal(dl, np.zeros(3))


def test_paired_bootstrap_is_deterministic_and_reports_direction():
    delta = np.array([-0.03, -0.02, -0.01, -0.04, -0.02])
    a = paired_bootstrap(delta, seed=17, draws=1000)
    b = paired_bootstrap(delta, seed=17, draws=1000)
    assert a == b
    assert a["mean_delta"] < 0
    assert a["bootstrap_probability_better_than_market"] == 1.0
    assert a["bootstrap_ci95_high"] < 0


def test_frozen_final_split_does_not_refit_on_validation_season():
    seasons = list(TRAIN_SEASONS) + [VALIDATION_SEASON, TEST_SEASON]
    frame = pd.DataFrame({"season": seasons, "row": range(len(seasons))})
    train, test = frozen_final_split(frame)
    assert list(train["season"]) == list(TRAIN_SEASONS)
    assert VALIDATION_SEASON not in set(train["season"])
    assert set(test["season"]) == {TEST_SEASON}

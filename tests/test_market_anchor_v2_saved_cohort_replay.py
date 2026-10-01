import numpy as np

import market_anchor_v2_saved_cohort_replay as replay


def _score(field: str):
    y = np.asarray([replay.RESULT_TO_INT[row["result"]] for row in replay.TARGETS], dtype=int)
    p = np.asarray([row[field] for row in replay.TARGETS], dtype=float)
    onehot = np.eye(3)[y]
    return {
        "accuracy": float((p.argmax(axis=1) == y).mean()),
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "log_loss": float(-np.mean(np.log(p[np.arange(len(y)), y]))),
    }


def test_saved_serie_a_cohort_is_exactly_ten_unique_events():
    replay.validate_targets()
    assert len(replay.TARGETS) == 10
    assert len({row["event_id"] for row in replay.TARGETS}) == 10
    assert replay.PRIMARY_LEAGUE == "SERIE_A"
    assert replay.FROZEN_PARENT_REPLAY_EVENTS == 47


def test_frozen_recipe_identity_is_not_tuned_in_replay():
    assert replay.FEATURE_VARIANT == "ALL_FOOTBALL"
    assert replay.SHADOW_LAMBDA == 1.0
    assert replay.L2_PENALTY == 1.0
    assert replay.FROZEN_V2_COMMIT == "df19777087fb89af049eedce44ff93f0aa6e6360"
    assert replay.HISTORY_CUTOFF_DATE.strftime("%Y-%m-%d") == "2026-09-11"


def test_saved_market_and_old_model_metrics_are_frozen():
    market = _score("market")
    old = _score("old_model")
    assert abs(market["accuracy"] - 0.6) <= 1e-15
    assert abs(market["brier"] - 0.5662948173955555) <= 1e-15
    assert abs(market["log_loss"] - 0.9674878846519602) <= 1e-15
    assert abs(old["accuracy"] - 0.5) <= 1e-15
    assert abs(old["brier"] - 0.5265153874268573) <= 1e-15
    assert abs(old["log_loss"] - 0.906202231280792) <= 1e-15


def test_frozen_source_blob_pins_cover_every_restored_module():
    assert replay.EXPECTED_FROZEN_GIT_BLOBS == {
        "historical_football_signal_lab.py": "401b3a0893371bfa4a488ec92a4a54af2678c8f7",
        "market_anchor_1x2_v1.py": "58c35bf3768f7bf2b951f19a37b9a5f46b6b9801",
        "market_anchor_1x2_v2_shadow.py": "b2770d726ffafe7a3cef706b57d3391063cbfe1b",
    }

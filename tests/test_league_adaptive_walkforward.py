import pandas as pd

import league_adaptive_walkforward as wf


def test_walkforward_has_multiple_seasons():
    assert (
        len(
            wf.WALKFORWARD_TEST_SEASONS
        )
        >= 4
    )


def test_small_segments_require_fallback():
    assert (
        wf.MIN_SEGMENT_ROWS
        > 1
    )

    assert (
        wf.MIN_CONFIDENCE_ROWS
        >= wf.MIN_SEGMENT_ROWS
    )


def test_policy_always_has_global_alpha():
    frame = pd.DataFrame({
        "target": [0, 1, 2] * 40,
        "ai_home_probability":
            [0.5, 0.3, 0.2] * 40,
        "ai_draw_probability":
            [0.3, 0.4, 0.3] * 40,
        "ai_away_probability":
            [0.2, 0.3, 0.5] * 40,
        "market_home_probability":
            [0.6, 0.3, 0.2] * 40,
        "market_draw_probability":
            [0.25, 0.4, 0.3] * 40,
        "market_away_probability":
            [0.15, 0.3, 0.5] * 40,
    })

    policy = wf.build_policy(
        frame
    )

    assert (
        "global_alpha"
        in policy
    )


def test_alpha_for_unknown_segment_falls_back_global():
    row = pd.Series({
        "segment": "UNKNOWN",
        "confidence_bucket": "UNKNOWN",
    })

    alpha, source = (
        wf.alpha_for_row(
            row,
            {
                "segments": {},
                "confidence": {},
                "global_alpha": 0.1,
            },
        )
    )

    assert alpha == 0.1
    assert source == "GLOBAL"


def test_alpha_zero_remains_available():
    assert (
        0.0
        in wf.adaptive.ALPHAS
    )

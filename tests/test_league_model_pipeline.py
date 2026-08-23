import league_model_pipeline as pipeline


def test_la_liga_pipeline_order():
    labels = [
        label
        for label, _
        in pipeline.LEAGUES[
            "LA_LIGA"
        ]["steps"]
    ]

    assert labels == [
        "historical_data",
        "normalization",
        "temporal_features",
        "elo",
        "oos",
    ]


def test_quality_gate_rejects_current_style_result():
    metrics = {
        "ai_accuracy": 0.52,
        "market_accuracy": 0.54,
        "home_accuracy": 0.45,
        "ai_logloss": 0.99,
        "market_logloss": 0.97,
        "ai_brier": 0.59,
        "market_brier": 0.57,
    }

    result = (
        pipeline.evaluate_quality(
            metrics
        )
    )

    assert (
        result[
            "ai_beats_home_baseline"
        ]
        is True
    )

    assert (
        result[
            "promotion_eligible"
        ]
        is False
    )


def test_quality_gate_accepts_market_beater():
    metrics = {
        "ai_accuracy": 0.56,
        "market_accuracy": 0.54,
        "home_accuracy": 0.45,
        "ai_logloss": 0.94,
        "market_logloss": 0.97,
        "ai_brier": 0.55,
        "market_brier": 0.57,
    }

    result = (
        pipeline.evaluate_quality(
            metrics
        )
    )

    assert (
        result[
            "promotion_eligible"
        ]
        is True
    )


def test_pipeline_never_contains_production_step():
    scripts = [
        script
        for _, script
        in pipeline.LEAGUES[
            "LA_LIGA"
        ]["steps"]
    ]

    forbidden = {
        "train_model_xgboost_elo.py",
        "train_model_no_odds.py",
        "promote_model.py",
    }

    assert not (
        set(scripts)
        & forbidden
    )

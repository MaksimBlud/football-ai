import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import market_anchor_1x2_v2_shadow as v2


ROOT = Path(__file__).resolve().parents[1]


def _artifact():
    features = list(v2.FEATURE_SETS[v2.FEATURE_VARIANT])
    body = {
        **v2.candidate_recipe(),
        "training_rows": 100,
        "training_fingerprint_sha256": "a" * 64,
        "imputer_medians": [0.0] * len(features),
        "scaler_mean": [0.0] * len(features),
        "scaler_scale": [1.0] * len(features),
        "weights": [[0.0, 0.0] for _ in range(len(features) + 1)],
    }
    body["artifact_sha256"] = v2._sha256_json(body)
    return body



def test_candidate_artifact_rejects_coercible_non_numeric_types():
    cases = [
        ("training_rows", True),
        ("training_rows", 100.5),
        ("training_rows", "100"),
        ("active_lambda", False),
        ("shadow_residual_lambda", True),
        ("l2_penalty", True),
        ("imputer_medians", ["0.0"] * 19),
        ("scaler_mean", [False] + [0.0] * 18),
        ("weights", [["0.0", "0.0"] for _ in range(20)]),
        ("training_fingerprint_sha256", int("1" * 64)),
    ]
    for field, value in cases:
        artifact = _artifact()
        artifact[field] = value
        body = dict(artifact)
        body.pop("artifact_sha256")
        artifact["artifact_sha256"] = v2._sha256_json(body)
        with pytest.raises(ValueError, match=field):
            v2.validate_candidate_artifact(artifact)

def test_candidate_artifact_rejects_integer_boolean_recipe_flags():
    cases = [
        ("stability_gate_passed", 0),
        ("opened_2026_27_outcomes_used", 0),
        ("research_only", 1),
        ("automatic_promotion", 0),
    ]
    for field, value in cases:
        artifact = _artifact()
        artifact[field] = value
        body = dict(artifact)
        body.pop("artifact_sha256")
        artifact["artifact_sha256"] = v2._sha256_json(body)
        with pytest.raises(ValueError, match=field):
            v2.validate_candidate_artifact(artifact)


def _row(**updates):
    row = {
        "experiment_id": v2.EXPERIMENT_ID,
        "evidence_class": v2.EVIDENCE_CLASS,
        "league": "SERIE_A",
        "event_id": "evt-1",
        "home_team": "Home",
        "away_team": "Away",
        "kickoff_utc": "2026-09-18T18:45:00Z",
        "capture_time_utc": "2026-09-18T17:00:00Z",
        "market_snapshot_time_utc": "2026-09-18T16:55:00Z",
        "incumbent_generated_at_utc": "2026-09-18T16:58:00Z",
        "candidate_generated_at_utc": "2026-09-18T16:59:00Z",
        "feature_history_cutoff_utc": "2026-09-18T16:50:00Z",
        "candidate_training_data_through_utc": "2026-06-30T23:59:59Z",
        "market_home_probability": 0.50,
        "market_draw_probability": 0.25,
        "market_away_probability": 0.25,
        "incumbent_home_probability": 0.48,
        "incumbent_draw_probability": 0.27,
        "incumbent_away_probability": 0.25,
        "candidate_home_probability": 0.50,
        "candidate_draw_probability": 0.25,
        "candidate_away_probability": 0.25,
        "shadow_residual_home_probability": 0.49,
        "shadow_residual_draw_probability": 0.26,
        "shadow_residual_away_probability": 0.25,
        "active_lambda": 0.0,
        "stability_gate_passed": False,
        "candidate_artifact_sha256": v2.FROZEN_CANDIDATE_ARTIFACT_SHA256,
        "incumbent_model_sha256": v2.INCUMBENT_MODEL_SHA256,
        "code_commit_sha": "c" * 40,
    }
    row.update(updates)
    return row


def test_protocol_inherits_v1_residual_but_fails_closed_to_market():
    source = json.loads((ROOT / "experiments/market_anchor_1x2_v1_report.json").read_text())
    serie_a = next(x for x in source["league_reports"] if x["league"] == "SERIE_A")
    protocol = json.loads((ROOT / "experiments/market_anchor_1x2_v2_protocol.json").read_text())

    assert serie_a["selected_feature_variant"] == "ALL_FOOTBALL"
    assert serie_a["selected_lambda"] == 1.0
    assert protocol["candidate_recipe"]["feature_variant"] == serie_a["selected_feature_variant"]
    assert protocol["candidate_recipe"]["shadow_residual_lambda"] == serie_a["selected_lambda"]
    assert protocol["candidate_recipe"]["active_lambda"] == 0.0
    assert protocol["candidate_recipe"]["active_mode"] == "MARKET_FALLBACK"
    assert protocol["candidate_recipe"]["stability_gate_passed"] is False
    assert protocol["candidate_recipe"]["use_opened_2026_27_outcomes_for_fit_or_selection"] is False
    assert protocol["primary_cohort"]["league"] == "SERIE_A"
    assert protocol["first_outcome_read_gate"]["completed_primary_events"] == 30
    assert protocol["decision_policy"]["automatic_promotion"] is False
    assert protocol["decision_policy"]["result"] == "NO_BET"


def test_frozen_v1_robustness_fails_the_predeclared_stability_gate():
    report = json.loads((ROOT / "experiments/market_anchor_1x2_v1_robustness_report.json").read_text())
    gate = v2.stability_gate(report)
    protocol = json.loads((ROOT / "experiments/market_anchor_1x2_v2_protocol.json").read_text())

    assert gate["passed"] is False
    assert gate["observed"]["prior_seasons"] == 6
    assert gate["observed"]["prior_dual_metric_wins"] == 2
    assert gate["checks"]["min_prior_dual_metric_wins"] is False
    assert gate["checks"]["brier_ci95_entirely_better_than_market"] is False
    assert gate["checks"]["log_loss_ci95_entirely_better_than_market"] is False
    assert gate["checks"]["brier_probability_better_at_least_95pct"] is False
    assert gate["checks"]["log_loss_probability_better_at_least_95pct"] is False
    assert protocol["stability_gate"]["passed"] is False
    assert protocol["provenance"]["source_robustness_report_blob_sha"] == v2.SOURCE_ROBUSTNESS_REPORT_BLOB_SHA


def test_candidate_recipe_refits_only_pre_2026_27_history():
    recipe = v2.candidate_recipe()
    assert recipe["primary_league"] == "SERIE_A"
    assert recipe["feature_variant"] == "ALL_FOOTBALL"
    assert recipe["shadow_residual_lambda"] == 1.0
    assert recipe["active_lambda"] == 0.0
    assert recipe["stability_gate_passed"] is False
    assert recipe["l2_penalty"] == 1.0
    assert recipe["refit_seasons"][-1] == "2025-2026"
    assert "2026-2027" not in recipe["refit_seasons"]
    assert recipe["opened_2026_27_outcomes_used"] is False
    assert len(recipe["features"]) == 19


def test_active_candidate_is_exact_market_even_when_shadow_residual_moves():
    artifact = _artifact()
    artifact["weights"][0] = [0.35, -0.20]
    body = dict(artifact)
    body.pop("artifact_sha256")
    artifact["artifact_sha256"] = v2._sha256_json(body)
    v2.validate_candidate_artifact(artifact)

    market = np.array([[0.50, 0.25, 0.25], [0.30, 0.30, 0.40]])
    features = pd.DataFrame(np.zeros((2, 19)), columns=artifact["features"])
    active = v2.predict_candidate(market, features, artifact)
    shadow = v2.predict_shadow_residual(market, features, artifact)

    np.testing.assert_allclose(active, market, atol=1e-12)
    assert not np.allclose(shadow, market, atol=1e-12)

    broken = dict(artifact)
    broken["active_lambda"] = 1.0
    with pytest.raises(ValueError, match="frozen recipe"):
        v2.validate_candidate_artifact(broken)


def test_shadow_capture_accepts_only_pre_kickoff_outcome_free_serie_a_rows():
    assert v2.validate_shadow_capture_rows([_row()])[0]["event_id"] == "evt-1"

    with pytest.raises(ValueError, match="outcome fields"):
        v2.validate_shadow_capture_rows([_row(result="H")])
    with pytest.raises(ValueError, match="only Serie A"):
        v2.validate_shadow_capture_rows([_row(league="EPL")])
    with pytest.raises(ValueError, match="pre-kickoff"):
        v2.validate_shadow_capture_rows([_row(capture_time_utc="2026-09-18T19:00:00Z")])
    with pytest.raises(ValueError, match="backfilled"):
        v2.validate_shadow_capture_rows([
            _row(kickoff_utc="2026-09-15T18:45:00Z", capture_time_utc="2026-09-15T17:00:00Z")
        ])
    with pytest.raises(ValueError, match="backfilled prediction inputs"):
        v2.validate_shadow_capture_rows([_row(market_snapshot_time_utc="2026-09-15T23:59:00Z")])


def test_shadow_capture_enforces_closed_gate_and_exact_market_fallback():
    with pytest.raises(ValueError, match="stability gate state"):
        v2.validate_shadow_capture_rows([_row(stability_gate_passed=True)])
    with pytest.raises(ValueError, match="active lambda"):
        v2.validate_shadow_capture_rows([_row(active_lambda=1.0)])
    with pytest.raises(ValueError, match="must equal market"):
        v2.validate_shadow_capture_rows([
            _row(candidate_home_probability=0.49, candidate_draw_probability=0.26)
        ])


def test_shadow_capture_requires_frozen_training_and_incumbent_identity():
    with pytest.raises(ValueError, match="training cutoff"):
        v2.validate_shadow_capture_rows([_row(candidate_training_data_through_utc="2026-09-01T00:00:00Z")])
    with pytest.raises(ValueError, match="incumbent model sha"):
        v2.validate_shadow_capture_rows([_row(incumbent_model_sha256="d" * 64)])


def test_shadow_capture_batch_cannot_mix_residual_artifacts():
    row2 = _row(
        event_id="evt-2",
        home_team="Home 2",
        away_team="Away 2",
        candidate_artifact_sha256="d" * 64,
    )
    with pytest.raises(ValueError, match="cannot mix candidate artifacts"):
        v2.validate_shadow_capture_rows([_row(), row2])


def test_shadow_capture_rejects_duplicate_fixture_under_distinct_event_ids():
    with pytest.raises(ValueError, match="duplicate canonical primary fixture"):
        v2.validate_shadow_capture_rows([_row(), _row(event_id="evt-2")])


def test_shadow_capture_rejects_reversed_fixture_and_v2_alias_duplicates():
    first = _row(home_team="Atalanta BC", away_team="Milan")
    second = _row(event_id="evt-2", home_team="AC Milan", away_team="Atalanta")
    with pytest.raises(ValueError, match="duplicate canonical primary fixture"):
        v2.validate_shadow_capture_rows([first, second])


def test_shadow_capture_rejects_runtime_alias_for_same_team_on_both_sides():
    with pytest.raises(ValueError, match="distinct teams"):
        v2.validate_shadow_capture_rows([_row(home_team="Milan", away_team="AC Milan")])


def test_shadow_capture_allows_same_clubs_on_distinct_local_match_dates():
    row2 = _row(
        event_id="evt-2",
        kickoff_utc="2026-09-19T18:45:00Z",
        capture_time_utc="2026-09-19T17:00:00Z",
        market_snapshot_time_utc="2026-09-19T16:55:00Z",
        incumbent_generated_at_utc="2026-09-19T16:58:00Z",
        candidate_generated_at_utc="2026-09-19T16:59:00Z",
        feature_history_cutoff_utc="2026-09-19T16:50:00Z",
    )
    assert len(v2.validate_shadow_capture_rows([_row(), row2])) == 2

def test_shadow_capture_rejects_same_fixture_with_different_kickoff_time_same_local_date():
    row2 = _row(event_id="evt-2", kickoff_utc="2026-09-18T20:00:00Z")
    with pytest.raises(ValueError, match="duplicate canonical primary fixture"):
        v2.validate_shadow_capture_rows([_row(), row2])


def test_shadow_identity_aliases_match_original_feature_manifest():
    from serie_a_v2_asof_feature_manifest import V2_HISTORICAL_TEAM_ALIASES

    assert v2.V2_HISTORICAL_TEAM_ALIASES == V2_HISTORICAL_TEAM_ALIASES


def test_outcome_gate_is_count_based_and_cannot_activate_v2_post_hoc():
    assert not v2.outcome_read_permitted(0)
    assert not v2.outcome_read_permitted(29)
    assert v2.outcome_read_permitted(30)
    assert v2.outcome_read_permitted(31)
    assert v2.ACTIVE_LAMBDA == 0.0
    assert v2.STABILITY_GATE_PASSED is False
    with pytest.raises(ValueError):
        v2.outcome_read_permitted(-1)


@pytest.mark.parametrize(
    "count",
    [True, False, np.bool_(True), 29.0, 30.0, 30.5, "30", None],
)
def test_outcome_gate_rejects_non_integer_event_counts(count):
    with pytest.raises(ValueError, match="nonnegative integer"):
        v2.outcome_read_permitted(count)


def test_outcome_gate_accepts_numpy_integer_count():
    assert v2.outcome_read_permitted(np.int64(30))


def _completed_gate_batch(count):
    captures = []
    metadata = []
    first_day = pd.Timestamp("2026-09-18")
    for index in range(count):
        day = (first_day + pd.Timedelta(days=index)).strftime("%Y-%m-%d")
        home = f"Home {index}"
        away = f"Away {index}"
        captures.append(_row(
            event_id=f"gate-event-{index}",
            home_team=home,
            away_team=away,
            kickoff_utc=f"{day}T18:45:00Z",
            capture_time_utc=f"{day}T17:00:00Z",
            market_snapshot_time_utc=f"{day}T16:55:00Z",
            incumbent_generated_at_utc=f"{day}T16:58:00Z",
            candidate_generated_at_utc=f"{day}T16:59:00Z",
            feature_history_cutoff_utc=f"{day}T16:50:00Z",
        ))
        metadata.append({
            "league": "SERIE_A",
            "season": v2.COMPLETED_PRIMARY_SEASON,
            "match_date": day,
            "home_team": home,
            "away_team": away,
            "source_updated_at_utc": f"{day}T21:00:00Z",
            "persisted_at_utc": f"{day}T21:01:00Z",
        })
    return captures, metadata


def _build_completed_gate(captures, metadata, **overrides):
    args = {
        "source_table": v2.COMPLETED_PRIMARY_METADATA_SOURCE_TABLE,
        "selected_columns": v2.COMPLETED_PRIMARY_METADATA_COLUMNS,
        "as_of_utc": "2026-11-23T12:00:00Z",
    }
    args.update(overrides)
    return v2.build_completed_primary_event_gate(captures, metadata, **args)


def test_completed_primary_gate_stays_closed_with_29_matched_captured_fixtures():
    captures, metadata = _completed_gate_batch(29)
    gate = _build_completed_gate(captures, metadata)
    assert gate["completed_primary_events"] == 29
    assert gate["outcome_read_permitted"] is False
    assert gate["target_outcomes_read"] is False
    assert gate["outcome_values_selected"] is False
    assert len(gate["completed_fixture_identity_sha256"]) == 64


def test_completed_primary_gate_opens_at_exactly_30_unique_matched_fixtures():
    captures, metadata = _completed_gate_batch(30)
    gate = _build_completed_gate(captures, metadata)
    assert gate["completed_primary_events"] == 30
    assert gate["outcome_read_permitted"] is True
    assert gate["validated_capture_rows"] == 30
    assert gate["metadata_rows_seen"] == 30
    assert gate["selected_columns"] == list(v2.COMPLETED_PRIMARY_METADATA_COLUMNS)
    assert gate["source_table"] == "public.league_finished_results"
    assert gate["target_outcomes_read"] is False
    assert gate["outcome_values_selected"] is False


def test_completed_primary_gate_counts_only_captured_fixtures_not_unmatched_results():
    captures, metadata = _completed_gate_batch(30)
    metadata.append({
        "league": "SERIE_A",
        "season": v2.COMPLETED_PRIMARY_SEASON,
        "match_date": "2026-10-20",
        "home_team": "Uncaptured Home",
        "away_team": "Uncaptured Away",
        "source_updated_at_utc": "2026-10-20T21:00:00Z",
        "persisted_at_utc": "2026-10-20T21:01:00Z",
    })
    gate = _build_completed_gate(captures, metadata)
    assert gate["metadata_rows_seen"] == 31
    assert gate["completed_primary_events"] == 30
    assert gate["outcome_read_permitted"] is True


def test_completed_primary_gate_uses_local_serie_a_fixture_date():
    capture = _row(
        home_team="Atalanta BC",
        away_team="Milan",
        kickoff_utc="2026-09-18T22:30:00Z",
        capture_time_utc="2026-09-18T21:00:00Z",
        market_snapshot_time_utc="2026-09-18T20:55:00Z",
        incumbent_generated_at_utc="2026-09-18T20:58:00Z",
        candidate_generated_at_utc="2026-09-18T20:59:00Z",
        feature_history_cutoff_utc="2026-09-18T20:50:00Z",
    )
    metadata = [{
        "league": "SERIE_A",
        "season": v2.COMPLETED_PRIMARY_SEASON,
        "match_date": "2026-09-19",
        "home_team": "Atalanta",
        "away_team": "AC Milan",
        "source_updated_at_utc": "2026-09-19T01:00:00Z",
        "persisted_at_utc": "2026-09-19T01:01:00Z",
    }]
    gate = _build_completed_gate([capture], metadata)
    assert gate["completed_primary_events"] == 1
    assert gate["outcome_read_permitted"] is False


@pytest.mark.parametrize("source_table", [
    "public.odds_snapshots",
    "public.predictions",
    "public.league_prediction_ledger",
])
def test_completed_primary_gate_rejects_unregistered_metadata_source(source_table):
    captures, metadata = _completed_gate_batch(30)
    with pytest.raises(ValueError, match="source table"):
        _build_completed_gate(captures, metadata, source_table=source_table)


def test_completed_primary_gate_rejects_any_result_or_extra_selected_column():
    captures, metadata = _completed_gate_batch(30)
    with pytest.raises(ValueError, match="exact outcome-free metadata columns"):
        _build_completed_gate(
            captures,
            metadata,
            selected_columns=(*v2.COMPLETED_PRIMARY_METADATA_COLUMNS, "home_goals"),
        )
    metadata[0]["home_goals"] = 2
    with pytest.raises(ValueError, match="only the exact preregistered metadata columns"):
        _build_completed_gate(captures, metadata)


def test_completed_primary_gate_rejects_wrong_season_and_non_primary_league():
    captures, metadata = _completed_gate_batch(1)
    wrong_season = [dict(metadata[0], season="2025-2026")]
    with pytest.raises(ValueError, match="outside the frozen primary season"):
        _build_completed_gate(captures, wrong_season)
    wrong_league = [dict(metadata[0], league="EPL")]
    with pytest.raises(ValueError, match="non-primary league"):
        _build_completed_gate(captures, wrong_league)


def test_completed_primary_gate_rejects_duplicate_completed_fixture_alias_rows():
    captures, metadata = _completed_gate_batch(1)
    trailing_space = [dict(metadata[0], home_team="Home 0 ", away_team="Away 0")]
    with pytest.raises(ValueError, match="canonical non-empty string"):
        _build_completed_gate(captures, trailing_space)
    captures[0]["home_team"] = "Atalanta BC"
    captures[0]["away_team"] = "Milan"
    alias_rows = [
        dict(metadata[0], home_team="Atalanta", away_team="AC Milan"),
        dict(metadata[0], home_team="Atalanta BC", away_team="Milan"),
    ]
    with pytest.raises(ValueError, match="duplicate completed canonical primary fixture"):
        _build_completed_gate(captures, alias_rows)


def test_completed_primary_gate_rejects_reversed_home_away_orientation():
    captures, metadata = _completed_gate_batch(1)
    reversed_metadata = [dict(metadata[0], home_team="Away 0", away_team="Home 0")]
    with pytest.raises(ValueError, match="orientation differs"):
        _build_completed_gate(captures, reversed_metadata)


def test_completed_primary_gate_rejects_invalid_or_naive_result_metadata_clocks():
    captures, metadata = _completed_gate_batch(1)
    naive = [dict(metadata[0], source_updated_at_utc="2026-09-18T21:00:00")]
    with pytest.raises(ValueError):
        _build_completed_gate(captures, naive)
    inverted = [dict(metadata[0], source_updated_at_utc="2026-09-18T21:02:00Z")]
    with pytest.raises(ValueError, match="not ordered"):
        _build_completed_gate(captures, inverted)
    future_persist = [dict(metadata[0], persisted_at_utc="2026-11-24T00:00:00Z")]
    with pytest.raises(ValueError, match="not ordered"):
        _build_completed_gate(captures, future_persist)


def test_completed_primary_gate_rejects_future_kickoff_even_if_metadata_is_supplied():
    captures, metadata = _completed_gate_batch(1)
    future_capture = dict(captures[0])
    future_capture["kickoff_utc"] = "2026-11-24T18:45:00Z"
    future_capture["capture_time_utc"] = "2026-11-24T17:00:00Z"
    future_capture["market_snapshot_time_utc"] = "2026-11-24T16:55:00Z"
    future_capture["incumbent_generated_at_utc"] = "2026-11-24T16:58:00Z"
    future_capture["candidate_generated_at_utc"] = "2026-11-24T16:59:00Z"
    future_capture["feature_history_cutoff_utc"] = "2026-11-24T16:50:00Z"
    future_metadata = [dict(metadata[0], match_date="2026-11-24",
                             source_updated_at_utc="2026-11-23T00:00:00Z",
                             persisted_at_utc="2026-11-23T01:00:00Z")]
    with pytest.raises(ValueError, match="kickoff is not before"):
        _build_completed_gate([future_capture], future_metadata)


def test_v2_code_does_not_reference_production_pickle_paths():
    text = (ROOT / "market_anchor_1x2_v2_shadow.py").read_text()
    assert "football_model_xgboost_elo.pkl" not in text
    assert "joblib.dump" not in text
    assert "--production" not in text


def test_saved_frozen_candidate_matches_original_artifact():
    candidate_path = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"
    raw = candidate_path.read_bytes()
    git_blob_sha1 = hashlib.sha1(
        f"blob {len(raw)}\0".encode("ascii") + raw
    ).hexdigest()
    assert git_blob_sha1 == "ac1303f6b096664983fbf52443bd0a381b23ba21"

    candidate = json.loads(raw)
    v2.validate_candidate_artifact(candidate)
    assert candidate["artifact_sha256"] == "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    assert candidate["training_fingerprint_sha256"] == "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
    assert candidate["training_rows"] == 3799
    assert candidate["features"] == list(v2.FEATURE_SETS[v2.FEATURE_VARIANT])
    assert len(candidate["features"]) == 19
    assert len(candidate["weights"]) == 20
    assert all(len(row) == 2 for row in candidate["weights"])
    assert candidate["active_lambda"] == 0.0
    assert candidate["shadow_residual_lambda"] == 1.0
    assert candidate["stability_gate_passed"] is False
    assert candidate["automatic_promotion"] is False
    assert candidate["opened_2026_27_outcomes_used"] is False


def test_frozen_stability_gate_rejects_coercible_scalar_types():
    base = json.loads(
        (ROOT / "experiments/market_anchor_1x2_v1_robustness_report.json").read_text()
    )
    cases = [
        ("frozen_lambda", "1.0"),
        ("frozen_lambda", True),
        ("retrospective_prior_seasons", "6"),
        ("retrospective_prior_seasons", 6.0),
        ("retrospective_prior_seasons", True),
        ("retrospective_prior_season_dual_wins", "2"),
        ("retrospective_prior_season_dual_wins", False),
    ]
    for field, value in cases:
        report = json.loads(json.dumps(base))
        report[field] = value
        with pytest.raises(ValueError, match=field):
            v2.stability_gate(report)


def test_frozen_stability_gate_rejects_coercible_or_nonfinite_bootstrap_metrics():
    base = json.loads(
        (ROOT / "experiments/market_anchor_1x2_v1_robustness_report.json").read_text()
    )
    cases = [
        ("final_oot_brier_bootstrap", "bootstrap_ci95_high", "0.003"),
        ("final_oot_brier_bootstrap", "bootstrap_ci95_high", True),
        ("final_oot_brier_bootstrap", "bootstrap_probability_better_than_market", float("nan")),
        ("final_oot_log_loss_bootstrap", "bootstrap_ci95_high", float("inf")),
        ("final_oot_log_loss_bootstrap", "bootstrap_probability_better_than_market", "0.63"),
        ("final_oot_log_loss_bootstrap", "bootstrap_probability_better_than_market", False),
    ]
    for section, field, value in cases:
        report = json.loads(json.dumps(base))
        report[section][field] = value
        with pytest.raises(ValueError, match=field):
            v2.stability_gate(report)


def test_frozen_stability_gate_rejects_non_mapping_bootstrap_sections():
    base = json.loads(
        (ROOT / "experiments/market_anchor_1x2_v1_robustness_report.json").read_text()
    )
    for section in ("final_oot_brier_bootstrap", "final_oot_log_loss_bootstrap"):
        report = json.loads(json.dumps(base))
        report[section] = []
        with pytest.raises(ValueError, match=section):
            v2.stability_gate(report)


def test_frozen_stability_gate_rejects_out_of_range_bootstrap_probabilities():
    base = json.loads(
        (ROOT / "experiments/market_anchor_1x2_v1_robustness_report.json").read_text()
    )
    fields = (
        ("final_oot_brier_bootstrap", "bootstrap_probability_better_than_market"),
        ("final_oot_log_loss_bootstrap", "bootstrap_probability_better_than_market"),
    )
    for section, field in fields:
        for value in (-0.001, 1.001):
            report = json.loads(json.dumps(base))
            report[section][field] = value
            with pytest.raises(ValueError, match="between 0 and 1"):
                v2.stability_gate(report)


def test_frozen_stability_gate_rejects_more_dual_wins_than_prior_seasons():
    report = json.loads(
        (ROOT / "experiments/market_anchor_1x2_v1_robustness_report.json").read_text()
    )
    report["retrospective_prior_season_dual_wins"] = (
        report["retrospective_prior_seasons"] + 1
    )
    with pytest.raises(ValueError, match="cannot exceed"):
        v2.stability_gate(report)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stability_gate_passed", 0),
        ("stability_gate_passed", None),
        ("active_lambda", "0"),
        ("active_lambda", False),
    ],
)
def test_shadow_capture_rejects_coerced_gate_and_lambda_types(field, value):
    with pytest.raises(ValueError, match=field):
        v2.validate_shadow_capture_rows([_row(**{field: value})])


@pytest.mark.parametrize(
    "field",
    [
        "market_home_probability",
        "incumbent_home_probability",
        "candidate_home_probability",
        "shadow_residual_home_probability",
    ],
)
def test_shadow_capture_rejects_coerced_probability_types(field):
    with pytest.raises(ValueError, match="probability"):
        v2.validate_shadow_capture_rows([_row(**{field: "0.5"})])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("event_id", 1),
        ("candidate_artifact_sha256", int("1" * 64)),
        ("code_commit_sha", int("1" * 40)),
    ],
)
def test_shadow_capture_rejects_non_string_identity_and_sha_fields(field, value):
    with pytest.raises(ValueError, match=field):
        v2.validate_shadow_capture_rows([_row(**{field: value})])


def test_shadow_capture_rejects_well_formed_non_frozen_candidate_sha():
    with pytest.raises(ValueError, match="frozen V2 candidate"):
        v2.validate_shadow_capture_rows([_row(candidate_artifact_sha256="b" * 64)])


@pytest.mark.parametrize(
    "field",
    ["incumbent_generated_at_utc", "candidate_generated_at_utc"],
)
def test_shadow_capture_rejects_prediction_generated_before_market_snapshot(field):
    with pytest.raises(ValueError, match="market snapshot must precede"):
        v2.validate_shadow_capture_rows([
            _row(**{field: "2026-09-18T16:54:00Z"})
        ])


@pytest.mark.parametrize(
    "feature_cutoff",
    ["2026-09-18T16:55:00Z", "2026-09-18T16:56:00Z"],
)
def test_shadow_capture_requires_feature_source_strictly_before_market_quote(feature_cutoff):
    with pytest.raises(ValueError, match="feature history cutoff must be strictly before"):
        v2.validate_shadow_capture_rows([
            _row(feature_history_cutoff_utc=feature_cutoff)
        ])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("incumbent_generated_at_utc", "2026-09-18T16:55:00Z"),
        ("candidate_generated_at_utc", "2026-09-18T16:55:00Z"),
        ("incumbent_generated_at_utc", "2026-09-18T17:00:00Z"),
        ("candidate_generated_at_utc", "2026-09-18T17:00:00Z"),
    ],
)
def test_shadow_capture_rejects_equal_quote_or_capture_timestamps(field, value):
    with pytest.raises(ValueError, match="strictly precede"):
        v2.validate_shadow_capture_rows([_row(**{field: value})])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("home_team", ""),
        ("home_team", "   "),
        ("home_team", None),
        ("home_team", 1),
        ("home_team", " Home "),
        ("away_team", ""),
        ("away_team", "   "),
        ("away_team", None),
        ("away_team", 1),
        ("away_team", " Away "),
    ],
)
def test_shadow_capture_rejects_invalid_team_identity_values(field, value):
    with pytest.raises(ValueError, match=field):
        v2.validate_shadow_capture_rows([_row(**{field: value})])


def test_shadow_capture_rejects_same_team_on_both_sides_after_normalization():
    with pytest.raises(ValueError, match="distinct teams"):
        v2.validate_shadow_capture_rows([_row(home_team="A  Team", away_team="a team")])


@pytest.mark.parametrize("event_id", [" evt-1", "evt-1 "])
def test_shadow_capture_rejects_noncanonical_event_id_whitespace(event_id):
    with pytest.raises(ValueError, match="canonical"):
        v2.validate_shadow_capture_rows([_row(event_id=event_id)])


@pytest.mark.parametrize("extra", [
    {"metadata": {"result": "H"}},
    {"audit": [{"score": "1-0"}]},
    {"provider": {"HC": 11, "FTAG": 2}},
    {"provider": {"HTHG": 1, "FTR": "H"}},
    {"stats": {"HST": 6, "AST": 3, "HF": 12, "AF": 9}},
    {"stats": {"home_corners": 9, "away_yellows": 3}},
    {"nested": [{"source": {"Home_Goals": 2}}]},
])
def test_shadow_capture_rejects_nested_raw_match_outcomes(extra):
    row = _row()
    row.update(extra)
    with pytest.raises(ValueError, match="outcome fields"):
        v2.validate_shadow_capture_rows([row])


@pytest.mark.parametrize("alias,value", [
    ("FTHG", 2), ("HG", 2), ("FTAG", 1), ("AG", 1),
    ("FTR", "H"), ("Res", "H"), ("HTHG", 1), ("HTAG", 0), ("HTR", "H"),
    ("HxG", 1.5), ("AxG", 0.7), ("HS", 14), ("AS", 8),
    ("HST", 5), ("AST", 2), ("HHW", 1), ("AHW", 0),
    ("HF", 11), ("AF", 13), ("HFKC", 10), ("AFKC", 9),
    ("HO", 2), ("AO", 1), ("HC", 7), ("AC", 4),
    ("HY", 2), ("AY", 1), ("HR", 0), ("AR", 1),
    ("HBP", 10), ("ABP", 25), ("Attendance", 12000),
])
def test_shadow_capture_rejects_all_documented_football_data_result_stat_aliases(alias, value):
    row = _row(provider_row={alias: value})
    with pytest.raises(ValueError, match="outcome fields"):
        v2.validate_shadow_capture_rows([row])


@pytest.mark.parametrize("payload", [
    {"provider_row": {"goals": {"home": 2, "away": 0}}},
    {"provider_row": {"goal": {"home": 2}}},
    {"provider_row": {"goals_scored": {"home": 2, "away": 0}}},
    {"provider_row": {"Home Goals": 2}},
    {"provider_row": {"home-goals": 2}},
    {"provider_row": {"homeTeamGoals": 2, "awayTeamGoals": 0}},
    {"provider_row": {"goalsHomeTeam": 2, "goalsAwayTeam": 0}},
    {"provider_row": {"homeTeamScore": 2, "awayTeamScore": 0}},
    {"provider_row": {"FTScore": {"home": 2, "away": 0}}},
    {"provider_row": {"scoreLine": "2-0"}},
    {"provider_row": {"fullTime": {"home": 2, "away": 0}}},
    {"provider_row": {"home.goals": 2}},
    {"provider_row": {"scores": [2, 0]}},
    {"provider_row": {"homeScores": 2, "awayScores": 0}},
    {"provider_row": {"scoresHomeTeam": 2, "scoresAwayTeam": 0}},
    {"provider_row": {"scoreFullTime": "2-0"}},
    {"provider_row": {"xGHome": 1.4, "xGAway": 0.6}},
])
def test_shadow_capture_rejects_generic_goals_containers_and_separator_aliases(payload):
    row = _row()
    row.update(payload)
    with pytest.raises(ValueError, match="outcome fields"):
        v2.validate_shadow_capture_rows([row])


def test_derived_frozen_goal_features_remain_allowed():
    row = _row(features={"diff_goals_for_5": 0.1, "diff_goals_against_5": -0.1})
    assert v2.validate_shadow_capture_rows([row])[0]["event_id"] == "evt-1"


@pytest.mark.parametrize("provider_row", [
    {"F.T.H.G": 2},
    {"H.G": 1},
    {"F-T-A-G": 1},
    {"H T R": "H"},
    {"H-X-G": 1.4},
    {"A.X.G": 0.7},
])
def test_shadow_capture_rejects_punctuation_separated_compact_outcome_aliases(provider_row):
    row = _row(provider_row=provider_row)
    with pytest.raises(ValueError, match="outcome fields"):
        v2.validate_shadow_capture_rows([row])


def test_compact_outcome_alias_guard_preserves_frozen_derived_feature_names():
    assert v2.is_forbidden_outcome_field("F.T.H.G")
    assert v2.is_forbidden_outcome_field("H.G")
    assert not v2.is_forbidden_outcome_field("diff_goals_for_5")


@pytest.mark.parametrize("provider_row", [
    {"home_win": True},
    {"away_win": True},
    {"home_won": True},
    {"away_won": True},
    {"is_home_winner": True},
    {"is_away_winner": True},
    {"homeTeamWon": True},
    {"winnerSide": "H"},
    {"winnerTeamId": 123},
    {"Result-1X2": "A"},
    {"outcome_1x2": "D"},
    {"draw_result": True},
    {"isDraw": True},
    {"was_draw": True},
    {"drawn": True},
    {"home_result": "W"},
    {"away_result": "L"},
])
def test_shadow_capture_rejects_explicit_1x2_winner_and_draw_outcome_aliases(provider_row):
    row = _row(provider_row=provider_row)
    with pytest.raises(ValueError, match="outcome fields"):
        v2.validate_shadow_capture_rows([row])


def test_1x2_outcome_alias_guard_preserves_pre_match_market_and_frozen_features():
    assert not v2.is_forbidden_outcome_field("home_odds")
    assert not v2.is_forbidden_outcome_field("draw_odds")
    assert not v2.is_forbidden_outcome_field("away_odds")
    assert not v2.is_forbidden_outcome_field("diff_points_5")
    assert not v2.is_forbidden_outcome_field("diff_goals_for_5")


@pytest.mark.parametrize(("descriptor_key", "descriptor_value"), [
    ("name", "FTR"),
    ("type", "Full Time Result"),
    ("stat", "Home Goals"),
    ("fieldName", "Result-1X2"),
    ("metric", "Winner Side"),
    ("label", "Draw Result"),
    ("statistic", "Corners"),
    ("name", "Yellow Cards"),
    ("type", "Shots On Target"),
    ("key", ["F.T.H.G"]),
    ("attribute", "Red Cards"),
    ("abbr", "FTR"),
    ("abbreviation", "Full Time Result"),
    ("shortName", "Home Goals"),
    ("shortCode", "Result-1X2"),
    ("statCode", "Corners"),
    ("statisticCode", "Red Cards"),
    ("fieldCode", "FTAG"),
    ("metricCode", "Winner Side"),
    ("attributeName", "Draw Result"),
    ("propertyName", "Away Goals"),
    ("displayName", "Yellow Cards"),
    ("shortName", "FT Result"),
    ("displayName", "Final Result"),
    ("abbreviation", "Fulltime Result"),
    ("metricName", "FT Outcome"),
    ("propertyName", "Full Time Outcome"),
    ("statId", "FTR"),
    ("statisticId", "Full Time Result"),
    ("fieldId", "FTAG"),
    ("metricId", "Winner Side"),
    ("attributeId", "Away Goals"),
    ("propertyId", "Draw Result"),
    ("dataKey", "HTR"),
    ("statKey", "Red Cards"),
    ("outcomeKey", "Final Result"),
    ("resultKey", "Home Goals"),
])
def test_shadow_capture_rejects_outcomes_encoded_as_typed_stat_descriptors(descriptor_key, descriptor_value):
    row = _row(provider_row={"statistics": [{descriptor_key: descriptor_value, "value": "H"}]})
    with pytest.raises(ValueError, match="outcome fields"):
        v2.validate_shadow_capture_rows([row])


def test_typed_stat_descriptor_guard_uses_exact_names_not_arbitrary_text():
    row = _row(provider_row={
        "statistics": [
            {"name": "Market 1X2", "value": "1X2"},
            {"type": "Home Win Probability", "value": 0.55},
            {"label": "Possession Trend", "value": 58},
            {"abbreviation": "Market 1X2", "value": "1X2"},
            {"shortName": "Home Win Probability", "value": 0.55},
            {"statId": "Market 1X2", "value": "1X2"},
            {"fieldId": "Home Win Probability", "value": 0.55},
            {"dataKey": "Possession Trend", "value": 58},
        ]
    })
    assert v2.validate_shadow_capture_rows([row])[0]["event_id"] == "evt-1"

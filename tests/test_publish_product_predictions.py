import pytest

from publish_product_predictions import (
    GOAL_ARTIFACT_FILENAMES,
    build_snapshot_rows,
    fixture_kickoff_utc,
    goal_artifact_bundle_sha256,
    resolve_event_ids,
)


GOAL_BUNDLE_SHA = "a" * 64


def prediction(*, include_goals=True):
    row = {
        "match_date": "2026-09-13",
        "match_time": "15:00",
        "home_team": "Manchester United",
        "away_team": "Arsenal",
        "home_team_model": "Man United",
        "away_team_model": "Arsenal",
        "prediction": "HOME",
        "prediction_strength": "MEDIUM",
        "model_agreement": "true",
        "home_probability": "0.55",
        "draw_probability": "0.25",
        "away_probability": "0.20",
    }
    if include_goals:
        row.update(
            {
                "expected_home_goals": "1.7",
                "expected_away_goals": "1.1",
                "expected_total_goals": "2.8",
                "over_2_5_probability": "0.60",
                "under_2_5_probability": "0.40",
                "btts_yes_probability": "0.52",
                "btts_no_probability": "0.48",
                "top_score": "2:1",
                "top_score_probability": "0.11",
            }
        )
    return row


def fixture(**overrides):
    row = {
        "match_date": "2026-09-13",
        "match_time": "15:00",
        "home_team": "Manchester United",
        "away_team": "Arsenal",
        "home_team_model": "Man United",
        "away_team_model": "Arsenal",
        "match_datetime_uk": "2026-09-13T15:00:00",
        "league": "EPL",
    }
    row.update(overrides)
    return row


def test_naive_uk_fixture_time_is_converted_with_london_dst():
    assert fixture_kickoff_utc(fixture()) == "2026-09-13T14:00:00+00:00"


def test_explicit_utc_kickoff_takes_precedence():
    row = fixture(commence_time_utc="2026-09-13T14:05:00Z")
    assert fixture_kickoff_utc(row) == "2026-09-13T14:05:00+00:00"


def test_goal_artifact_bundle_hash_is_deterministic_and_covers_all_artifacts(tmp_path):
    paths = {}
    for index, filename in enumerate(GOAL_ARTIFACT_FILENAMES):
        path = tmp_path / filename
        path.write_bytes(f"artifact-{index}".encode("utf-8"))
        paths[filename] = path

    first = goal_artifact_bundle_sha256(paths)
    second = goal_artifact_bundle_sha256(dict(reversed(list(paths.items()))))

    assert len(first) == 64
    assert first == second

    paths[GOAL_ARTIFACT_FILENAMES[-1]].write_bytes(b"changed-calibrator")
    assert goal_artifact_bundle_sha256(paths) != first


def test_goal_artifact_bundle_rejects_partial_bundle(tmp_path):
    paths = {}
    for filename in GOAL_ARTIFACT_FILENAMES[:-1]:
        path = tmp_path / filename
        path.write_bytes(filename.encode("utf-8"))
        paths[filename] = path

    with pytest.raises(ValueError, match="exactly the four required artifacts"):
        goal_artifact_bundle_sha256(paths)


def test_goal_outputs_require_complete_bundle_provenance():
    with pytest.raises(ValueError, match="four-artifact goal inference bundle"):
        build_snapshot_rows(
            [prediction()],
            [fixture()],
            league="EPL",
            run_id="run-1",
            generated_at_utc="2026-09-12T07:00:00+00:00",
        )


def test_1x2_only_snapshot_does_not_require_goal_bundle_provenance():
    rows = build_snapshot_rows(
        [prediction(include_goals=False)],
        [fixture()],
        league="EPL",
        run_id="run-1",
        generated_at_utc="2026-09-12T07:00:00+00:00",
    )

    assert rows[0]["model_goals_sha256"] is None
    assert rows[0]["over_2_5_probability"] is None


def test_snapshot_builder_keeps_model_output_separate_from_market_price():
    rows = build_snapshot_rows(
        [prediction()],
        [fixture()],
        league="EPL",
        run_id="run-1",
        generated_at_utc="2026-09-12T07:00:00+00:00",
        model_1x2_version="production-1x2",
        model_1x2_sha256="abc123",
        model_goals_sha256=GOAL_BUNDLE_SHA,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["snapshot_schema_version"] == "product-prediction.v1"
    assert row["home_probability"] == pytest.approx(0.55)
    assert row["commence_time_utc"] == "2026-09-13T14:00:00+00:00"
    assert row["event_id"] is None
    assert "home_odds" not in row
    assert row["model_1x2_sha256"] == "abc123"
    assert row["model_goals_sha256"] == GOAL_BUNDLE_SHA


def test_missing_exact_fixture_is_rejected():
    bad_fixture = fixture(match_time="17:30")
    with pytest.raises(ValueError, match="no exact fixture row"):
        build_snapshot_rows(
            [prediction(include_goals=False)],
            [bad_fixture],
            league="EPL",
            run_id="run-1",
            generated_at_utc="2026-09-12T07:00:00+00:00",
        )


def test_event_id_can_be_resolved_from_stored_odds_without_api_call():
    rows = build_snapshot_rows(
        [prediction(include_goals=False)],
        [fixture()],
        league="EPL",
        run_id="run-1",
        generated_at_utc="2026-09-12T07:00:00+00:00",
    )
    odds = [
        {
            "league": "EPL",
            "event_id": "odds-event-1",
            "commence_time_utc": "2026-09-13T14:00:00+00:00",
            "home_team": "Manchester United",
            "away_team": "Arsenal",
        }
    ]

    assert resolve_event_ids(rows, odds) == 1
    assert rows[0]["event_id"] == "odds-event-1"


def test_ambiguous_stored_event_ids_are_not_guessed():
    rows = build_snapshot_rows(
        [prediction(include_goals=False)],
        [fixture()],
        league="EPL",
        run_id="run-1",
        generated_at_utc="2026-09-12T07:00:00+00:00",
    )
    odds = [
        {
            "league": "EPL",
            "event_id": event_id,
            "commence_time_utc": "2026-09-13T14:00:00+00:00",
            "home_team": "Manchester United",
            "away_team": "Arsenal",
        }
        for event_id in ("event-a", "event-b")
    ]

    assert resolve_event_ids(rows, odds) == 0
    assert rows[0]["event_id"] is None

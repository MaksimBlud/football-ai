from pathlib import Path


WORKFLOW = Path(".github/workflows/odds-snapshots.yml")
LIVE_CYCLE_WORKFLOW = Path(".github/workflows/epl-live-cycle.yml")
REQUIREMENTS = Path("requirements.txt")


def test_epl_odds_workflow_installs_full_shadow_runtime():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    requirements = REQUIREMENTS.read_text(encoding="utf-8")

    assert "pip install -r requirements.txt" in workflow
    assert "scheduled_odds_snapshot.py" in workflow

    # Challenger shadow imports the no-odds prediction runtime after a
    # successful snapshot, so the scheduled job must provide these packages.
    for dependency in ("joblib", "numpy", "scikit-learn", "xgboost"):
        assert dependency in requirements


def test_epl_odds_workflow_does_not_train_or_promote_models():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    forbidden = (
        "train_model",
        "--production",
        "joblib.dump",
        "football_model_xgboost_elo.pkl",
    )

    for token in forbidden:
        assert token not in workflow


def test_epl_live_cycle_does_not_claim_automatic_paid_snapshot_schedule():
    live_cycle = LIVE_CYCLE_WORKFLOW.read_text(encoding="utf-8")

    assert "Paid EPL odds snapshots are intentionally manual-only" in live_cycle
    assert "Odds snapshots run at :17 every two hours" not in live_cycle
    assert "THE_ODDS_API_KEY" not in live_cycle
    assert "scheduled_odds_snapshot.py" not in live_cycle

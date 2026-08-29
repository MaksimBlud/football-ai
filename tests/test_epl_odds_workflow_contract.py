from pathlib import Path


WORKFLOW = Path(".github/workflows/odds-snapshots.yml")
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

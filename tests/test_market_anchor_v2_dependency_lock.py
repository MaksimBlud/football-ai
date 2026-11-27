"""Reproducibility contract for the original V2 shadow validation environment."""
from importlib.metadata import version
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "requirements" / "market-anchor-v2-shadow-py311.lock"
WORKFLOW = ROOT / ".github" / "workflows" / "market-anchor-1x2-v2-shadow-validation.yml"

EXPECTED = {
    "certifi": "2026.11.20",
    "charset-normalizer": "3.5.3",
    "cloudpickle": "3.1.3",
    "idna": "3.20",
    "iniconfig": "2.3.1",
    "joblib": "1.6.0",
    "narwhals": "2.29.0",
    "numpy": "2.4.6",
    "packaging": "26.4",
    "pandas": "3.1.1",
    "pluggy": "1.7.0",
    "pygments": "2.21.0",
    "pytest": "9.2.0",
    "python-dateutil": "4.0.0",
    "requests": "2.34.2",
    "scikit-learn": "1.9.1",
    "scipy": "1.17.1",
    "threadpoolctl": "3.8.0",
    "tzdata": "2026.6",
    "urllib3": "2.8.0",
}


def _read_lock():
    entries = {}
    for raw in LOCK.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)", line)
        assert match is not None, f"lock entry is not an exact version pin: {line}"
        name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        assert name not in entries, f"duplicate lock entry: {name}"
        entries[name] = match.group(2)
    return entries


def test_lock_is_exact_and_matches_the_successful_python311_shadow_run():
    assert _read_lock() == EXPECTED


def test_running_environment_matches_every_locked_distribution():
    assert {name: version(name) for name in EXPECTED} == EXPECTED


def test_shadow_workflow_installs_lock_runs_pip_check_and_keeps_checkout_read_only():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'python-version: "3.11"' in workflow
    assert "python -m pip install -r requirements/market-anchor-v2-shadow-py311.lock" in workflow
    assert "python -m pip check" in workflow
    assert "persist-credentials: false" in workflow
    assert "tests/test_market_anchor_v2_dependency_lock.py" in workflow
    assert "requirements/market-anchor-v2-shadow-py311.lock" in workflow

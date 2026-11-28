from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
LOCK_DIR = ROOT / "research" / "locks"
LOCKS = {
    "3.11": LOCK_DIR / "market-anchor-v2-forward-py311.lock",
    "3.12": LOCK_DIR / "market-anchor-v2-forward-py312.lock",
}
PY312_WORKFLOWS = (
    ".github/workflows/serie-a-v2-forward-preview.yml",
    ".github/workflows/serie-a-v2-current-form-source-capture.yml",
    ".github/workflows/serie-a-v2-current-form-forward-preview.yml",
    ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml",
)


def _parse_lock(path):
    entries = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        assert re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+!-]+", line), line
        name, version = line.split("==", 1)
        entries.append((name.lower().replace("_", "-"), version))
    names = [name for name, _ in entries]
    assert len(names) == len(set(names)), f"duplicate package in {path}"
    return dict(entries)


def test_original_forward_python_locks_are_complete_exact_version_sets():
    locks = {version: _parse_lock(path) for version, path in LOCKS.items()}
    assert len(locks["3.11"]) >= 45
    assert len(locks["3.12"]) == len(locks["3.11"])
    assert set(locks["3.11"]) == set(locks["3.12"])
    differences = {
        name for name in locks["3.11"]
        if locks["3.11"][name] != locks["3.12"][name]
    }
    assert not differences, f"cross-Python lock drift: {sorted(differences)}"
    assert locks["3.11"]["numpy"] == locks["3.12"]["numpy"] == "2.4.6"
    assert locks["3.11"]["scipy"] == locks["3.12"]["scipy"] == "1.17.1"
    for name in ("pandas", "scikit-learn", "requests", "supabase", "pytest"):
        assert locks["3.11"][name] == locks["3.12"][name]


def test_original_forward_validation_installs_the_python_specific_lock():
    workflow = (ROOT / ".github/workflows/market-anchor-v2-original-forward-source-first-validation.yml").read_text()
    assert 'python-version: "3.11"' in workflow
    assert 'python-version: "3.12"' in workflow
    assert "market-anchor-v2-forward-py311.lock" in workflow
    assert "market-anchor-v2-forward-py312.lock" in workflow
    assert 'python -m pip install -r "${{ matrix.requirements-file }}"' in workflow
    assert "python -m pip check" in workflow
    assert "python -m pip install --upgrade pip" not in workflow
    assert "tests/test_serie_a_v2_forward_runtime_lock.py" in workflow


def test_original_v2_read_only_workflows_use_the_same_python312_lock():
    for relative in PY312_WORKFLOWS:
        workflow = (ROOT / relative).read_text()
        assert "python -m pip install -r research/locks/market-anchor-v2-forward-py312.lock" in workflow, relative
        assert "python -m pip check" in workflow, relative
        assert "python -m pip install pandas numpy scipy scikit-learn requests supabase python-dotenv pytest" not in workflow, relative


def test_live_access_and_schedules_remain_default_deny_and_unchanged():
    for relative in PY312_WORKFLOWS:
        workflow = (ROOT / relative).read_text()
        assert 'MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED: "false"' in workflow, relative
    original = (ROOT / ".github/workflows/serie-a-v2-forward-preview.yml").read_text()
    assert 'cron: "8 8 * * *"' in original
    source = (ROOT / ".github/workflows/serie-a-v2-current-form-source-capture.yml").read_text()
    assert 'cron: "50 5 * * *"' in source
    current_form = (ROOT / ".github/workflows/serie-a-v2-current-form-forward-preview.yml").read_text()
    assert 'cron: "18 8 * * *"' in current_form
    diagnostic = (ROOT / ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml").read_text()
    assert 'cron: "13 6 * * *"' in diagnostic

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_exact_lock(filename: str) -> dict[str, str]:
    path = ROOT / filename
    entries: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9][A-Za-z0-9.!+_-]*)", line)
        assert match, f"{filename} contains a non-exact package pin: {line!r}"
        normalized_name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        assert normalized_name not in entries, f"{filename} repeats {normalized_name}"
        entries[normalized_name] = match.group(2)
    assert len(entries) >= 45, f"{filename} is not a complete observed environment lock"
    return entries


def test_python_minor_locks_match_successful_observed_v2_environments() -> None:
    py311 = _read_exact_lock("requirements-v2-research-py311.lock")
    py312 = _read_exact_lock("requirements-v2-research-py312.lock")

    required = {
        "pip", "numpy", "pandas", "scipy", "scikit-learn",
        "requests", "supabase", "pytest", "httpx", "postgrest",
    }
    assert required <= py311.keys()
    assert required | {"python-dotenv"} <= py312.keys()

    assert py311["pip"] == py312["pip"] == "26.2.2"
    assert py311["numpy"] == "2.4.6"
    assert py312["numpy"] == "2.5.4"
    assert py311["scipy"] == "1.17.1"
    assert py312["scipy"] == "1.18.1"
    assert py311["pandas"] == py312["pandas"] == "3.1.0"
    assert py311["scikit-learn"] == py312["scikit-learn"] == "1.9.1"
    assert py311["requests"] == py312["requests"] == "2.34.2"
    assert py311["supabase"] == py312["supabase"] == "2.33.0"
    assert py311["pytest"] == py312["pytest"] == "9.2.0"


def test_original_v2_workflows_use_python_specific_exact_locks() -> None:
    py312_workflows = {
        ".github/workflows/serie-a-v2-current-form-source-capture.yml": "50 5 * * *",
        ".github/workflows/serie-a-v2-forward-preview.yml": "8 8 * * *",
        ".github/workflows/serie-a-v2-current-form-forward-preview.yml": "18 8 * * *",
        ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml": "13 6 * * *",
    }
    for relative_path, expected_cron in py312_workflows.items():
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        assert 'python-version: "3.12"' in content, relative_path
        assert "python -m pip install -r requirements-v2-research-py312.lock" in content
        assert "requirements-v2-research-py312.lock" in content
        assert f'cron: "{expected_cron}"' in content, f"schedule drift in {relative_path}"
        assert "python -m pip install pandas numpy scipy scikit-learn requests supabase" not in content

    shadow = (ROOT / ".github/workflows/serie-a-frozen-v2-shadow-tests.yml").read_text(encoding="utf-8")
    assert 'python-version: "3.11"' in shadow
    assert "python -m pip install -r requirements-v2-research-py311.lock" in shadow
    assert "tests/test_serie_a_v2_dependency_lock_contract.py" in shadow
    assert "requirements-v2-research-py311.lock" in shadow
    assert "requirements-v2-research-py312.lock" in shadow
    assert "cron:" not in shadow

    py312_job = shadow.split("  py312-lock-tests:\\n", 1)[1]
    assert 'python-version: "3.12"' in py312_job
    assert "python -m pip install -r requirements-v2-research-py312.lock" in py312_job
    assert "python -m pip check" in py312_job
    assert "tests/test_serie_a_v2_current_form_source_capture.py" in py312_job
    assert "tests/test_serie_a_v2_current_form_forward_capture.py" in py312_job

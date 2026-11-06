from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

from market_anchor_v2_frozen_runtime_attestation import (
    EXPECTED_CANDIDATE_ARTIFACT_SHA256,
    EXPECTED_CANDIDATE_GIT_BLOB_SHA,
    EXPECTED_FROZEN_GIT_BLOBS,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "market_anchor_v2_frozen_runtime_attestation.py"
CANDIDATE = ROOT / "research/models/market_anchor_v2_serie_a_frozen_candidate.json"


def _run(source_dir: Path, candidate_path: Path = CANDIDATE):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--frozen-source-dir",
            str(source_dir),
            "--candidate-path",
            str(candidate_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_original_frozen_v2_candidate_executes_on_synthetic_input_only():
    result = _run(ROOT)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["schema_version"] == "MARKET_ANCHOR_V2_FROZEN_RUNTIME_ATTESTATION_V1"
    assert report["mode"] == "SYNTHETIC_ONLY_RUNTIME_SMOKE"
    assert report["candidate_artifact_sha256"] == EXPECTED_CANDIDATE_ARTIFACT_SHA256
    assert report["candidate_git_blob_sha"] == EXPECTED_CANDIDATE_GIT_BLOB_SHA
    assert report["frozen_source_git_blobs"] == EXPECTED_FROZEN_GIT_BLOBS
    assert report["feature_count"] == 19
    assert report["weights_shape"] == [20, 2]
    assert report["active_lambda"] == 0.0
    assert report["shadow_lambda"] == 1.0
    assert report["stability_gate_passed"] is False
    assert report["active_equals_market_exactly"] is True
    assert report["shadow_output_finite"] is True
    assert report["shadow_probabilities_sum_to_one"] is True
    assert report["real_events_scored"] == 0
    assert report["target_outcomes_read"] is False
    assert report["training_performed"] is False
    assert report["production_pkl_touched"] is False
    assert report["automatic_promotion"] is False
    assert report["no_bet"] is True


def test_runtime_attestation_rejects_a_changed_frozen_source_blob(tmp_path):
    source = tmp_path / "frozen"
    source.mkdir()
    for filename in EXPECTED_FROZEN_GIT_BLOBS:
        shutil.copy2(ROOT / filename, source / filename)
    with (source / "market_anchor_1x2_v2_shadow.py").open("a", encoding="utf-8") as handle:
        handle.write("\n# deliberate test-only mutation\n")
    result = _run(source)
    assert result.returncode != 0
    assert "frozen source Git blob SHA mismatch" in result.stderr


def test_runtime_attestation_rejects_a_changed_candidate_blob(tmp_path):
    candidate = tmp_path / "candidate.json"
    candidate.write_bytes(CANDIDATE.read_bytes() + b" ")
    result = _run(ROOT, candidate)
    assert result.returncode != 0
    assert "frozen candidate Git blob SHA mismatch" in result.stderr

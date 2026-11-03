"""Run the original frozen MARKET_ANCHOR_1X2_V2 on synthetic inputs only.

This is a runtime-integrity smoke test, not a real-match forecast, training run,
prospective observation, model-quality claim, or promotion signal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

FROZEN_V2_COMMIT = "df19777087fb89af049eedce44ff93f0aa6e6360"
EXPECTED_CANDIDATE_ARTIFACT_SHA256 = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
EXPECTED_CANDIDATE_GIT_BLOB_SHA = "ac1303f6b096664983fbf52443bd0a381b23ba21"
EXPECTED_TRAINING_FINGERPRINT_SHA256 = "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
EXPECTED_TRAINING_ROWS = 3799
EXPECTED_FROZEN_GIT_BLOBS = {
    "historical_football_signal_lab.py": "401b3a0893371bfa4a488ec92a4a54af2678c8f7",
    "market_anchor_1x2_v1.py": "58c35bf3768f7bf2b951f19a37b9a5f46b6b9801",
    "market_anchor_1x2_v2_shadow.py": "b2770d726ffafe7a3cef706b57d3391063cbfe1b",
}


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    header = f"blob {len(raw)}".encode("ascii") + bytes((0,))
    return hashlib.sha1(header + raw).hexdigest()


def _load_frozen_modules(source_dir: Path):
    source_dir = source_dir.resolve()
    for name in (
        "historical_football_signal_lab",
        "market_anchor_1x2_v1",
        "market_anchor_1x2_v2_shadow",
    ):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(source_dir))
    try:
        import historical_football_signal_lab as feature_builder
        import market_anchor_1x2_v1 as v1
        import market_anchor_1x2_v2_shadow as v2
    finally:
        try:
            sys.path.remove(str(source_dir))
        except ValueError:
            pass
    return feature_builder, v1, v2


def run_attestation(source_dir: Path, candidate_path: Path) -> dict:
    source_dir = Path(source_dir)
    candidate_path = Path(candidate_path)

    observed_blobs = {}
    for filename, expected_sha in EXPECTED_FROZEN_GIT_BLOBS.items():
        path = source_dir / filename
        if not path.is_file():
            raise RuntimeError(f"frozen source file is missing: {filename}")
        observed = git_blob_sha(path)
        observed_blobs[filename] = observed
        if observed != expected_sha:
            raise RuntimeError(f"frozen source Git blob SHA mismatch: {filename}")

    candidate_blob_sha = git_blob_sha(candidate_path)
    if candidate_blob_sha != EXPECTED_CANDIDATE_GIT_BLOB_SHA:
        raise RuntimeError("frozen candidate Git blob SHA mismatch")

    candidate_raw = candidate_path.read_bytes()
    candidate = json.loads(candidate_raw)
    if candidate.get("artifact_sha256") != EXPECTED_CANDIDATE_ARTIFACT_SHA256:
        raise RuntimeError("frozen candidate artifact SHA mismatch")
    if candidate.get("training_fingerprint_sha256") != EXPECTED_TRAINING_FINGERPRINT_SHA256:
        raise RuntimeError("frozen candidate training fingerprint mismatch")
    if candidate.get("training_rows") != EXPECTED_TRAINING_ROWS:
        raise RuntimeError("frozen candidate training row count mismatch")
    if candidate.get("opened_2026_27_outcomes_used") is not False:
        raise RuntimeError("candidate must prove that protected 2026/27 outcomes were not used")
    if candidate.get("automatic_promotion") is not False or candidate.get("research_only") is not True:
        raise RuntimeError("candidate is not marked research-only and non-promotable")

    feature_builder, _v1, v2 = _load_frozen_modules(source_dir)
    v2.validate_candidate_artifact(candidate)
    expected_features = list(feature_builder.FEATURE_SETS["ALL_FOOTBALL"])
    if len(expected_features) != 19 or candidate.get("features") != expected_features:
        raise RuntimeError("candidate feature names/order do not match the frozen 19-feature builder")
    weights = np.asarray(candidate.get("weights"), dtype=float)
    if weights.shape != (20, 2) or not np.isfinite(weights).all():
        raise RuntimeError("candidate weights must be a finite 20x2 matrix")
    if (
        v2.ACTIVE_LAMBDA != 0.0
        or v2.SHADOW_RESIDUAL_LAMBDA != 1.0
        or v2.STABILITY_GATE_PASSED is not False
        or candidate.get("active_lambda") != 0.0
        or candidate.get("shadow_residual_lambda") != 1.0
        or candidate.get("stability_gate_passed") is not False
    ):
        raise RuntimeError("original V2 lambda/stability contract drifted")

    # Deliberately synthetic input: no event, real teams, quote, or outcome.
    synthetic_values = np.linspace(-0.75, 0.75, num=19, dtype=float)
    synthetic_features = pd.DataFrame([synthetic_values], columns=expected_features)
    synthetic_market = np.asarray([[0.45, 0.28, 0.27]], dtype=float)

    active = np.asarray(
        v2.predict_candidate(synthetic_market, synthetic_features, candidate),
        dtype=float,
    )
    shadow = np.asarray(
        v2.predict_shadow_residual(synthetic_market, synthetic_features, candidate),
        dtype=float,
    )
    if active.shape != (1, 3) or not np.isfinite(active).all():
        raise RuntimeError("active V2 output is not a finite 1x3 probability vector")
    if not np.allclose(active, synthetic_market, rtol=0.0, atol=1e-12):
        raise RuntimeError("active_lambda=0 must return the market probabilities exactly")
    if shadow.shape != (1, 3) or not np.isfinite(shadow).all():
        raise RuntimeError("shadow V2 output is not a finite 1x3 probability vector")
    if (shadow < 0.0).any() or (shadow > 1.0).any():
        raise RuntimeError("shadow V2 output is outside probability bounds")
    if not np.allclose(shadow.sum(axis=1), np.ones(1), rtol=0.0, atol=1e-12):
        raise RuntimeError("shadow V2 probabilities do not sum to one")

    synthetic_input = {
        "features": [float(x) for x in synthetic_values],
        "market": [float(x) for x in synthetic_market[0]],
    }
    synthetic_output = {
        "active": [float(x) for x in active[0]],
        "shadow": [float(x) for x in shadow[0]],
    }
    return {
        "schema_version": "MARKET_ANCHOR_V2_FROZEN_RUNTIME_ATTESTATION_V1",
        "mode": "SYNTHETIC_ONLY_RUNTIME_SMOKE",
        "frozen_v2_commit": FROZEN_V2_COMMIT,
        "candidate_artifact_sha256": candidate["artifact_sha256"],
        "candidate_git_blob_sha": candidate_blob_sha,
        "training_fingerprint_sha256": candidate["training_fingerprint_sha256"],
        "training_rows": candidate["training_rows"],
        "frozen_source_git_blobs": observed_blobs,
        "feature_count": len(expected_features),
        "weights_shape": list(weights.shape),
        "active_lambda": 0.0,
        "shadow_lambda": 1.0,
        "stability_gate_passed": False,
        "active_equals_market_exactly": True,
        "shadow_output_finite": True,
        "shadow_probabilities_sum_to_one": True,
        "synthetic_input_sha256": hashlib.sha256(
            json.dumps(synthetic_input, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "synthetic_output_sha256": hashlib.sha256(
            json.dumps(synthetic_output, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "real_events_scored": 0,
        "target_outcomes_read": False,
        "training_performed": False,
        "production_pkl_touched": False,
        "automatic_promotion": False,
        "no_bet": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-source-dir", type=Path, required=True)
    parser.add_argument(
        "--candidate-path",
        type=Path,
        default=Path("research/models/market_anchor_v2_serie_a_frozen_candidate.json"),
    )
    args = parser.parse_args()
    result = run_attestation(args.frozen_source_dir, args.candidate_path)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

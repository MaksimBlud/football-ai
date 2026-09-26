"""Deterministic safety gates for Football AI research-agent tasks."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PRODUCTION_ARTIFACTS = {
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
}

FORBIDDEN_COMMAND_FRAGMENTS = (
    "artifact_lifecycle.py promote",
    "git push origin main",
    "git checkout main",
    "git switch main",
    "supabase db reset",
    "supabase migration",
)

FORBIDDEN_PATH_SUFFIXES = (".pkl",)
FORBIDDEN_EXACT_PATHS = {
    "turkey_super_lig_runtime_config.py",
    "primeira_liga_runtime_config.py",
}

ALLOWED_MODES = {"historical_read_only"}


@dataclass(frozen=True)
class SafetyResult:
    ok: bool
    errors: tuple[str, ...]


def validate_mode(mode: str) -> SafetyResult:
    if mode not in ALLOWED_MODES:
        return SafetyResult(False, (f"unsupported mode: {mode}",))
    return SafetyResult(True, ())


def validate_commands(commands: Iterable[str]) -> SafetyResult:
    errors: list[str] = []
    for command in commands:
        lowered = command.lower()
        for fragment in FORBIDDEN_COMMAND_FRAGMENTS:
            if fragment.lower() in lowered:
                errors.append(f"forbidden command fragment: {fragment}")
    return SafetyResult(not errors, tuple(errors))


def validate_changed_paths(paths: Iterable[str]) -> SafetyResult:
    errors: list[str] = []
    for raw in paths:
        path = raw.strip()
        if not path:
            continue
        name = Path(path).name
        if name in PRODUCTION_ARTIFACTS or path.endswith(FORBIDDEN_PATH_SUFFIXES):
            errors.append(f"production artifact change forbidden: {path}")
        if path in FORBIDDEN_EXACT_PATHS:
            errors.append(f"runtime mutation forbidden in V1: {path}")
    return SafetyResult(not errors, tuple(errors))


def merge_results(*results: SafetyResult) -> SafetyResult:
    errors = tuple(error for result in results for error in result.errors)
    return SafetyResult(not errors, errors)

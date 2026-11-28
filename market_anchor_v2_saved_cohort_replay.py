"""Permanently retired compatibility surface for the old saved-cohort V2 replay.

The original MARKET_ANCHOR_1X2_V2 candidate is SHA-pinned and its saved-cohort
replay/refit path is no longer an approved operation. Keep only fail-closed
entrypoints for old workflow callers. This module intentionally has no network,
filesystem, database, target-outcome, model-fitting, or artifact-writing code.
"""
from __future__ import annotations

RETIREMENT_MESSAGE = (
    "saved-cohort replay/refit is permanently retired; use only the separately "
    "authorized pre-kickoff original V2 forward path"
)


def _deny_retired_saved_cohort_replay() -> None:
    raise PermissionError(RETIREMENT_MESSAGE)


def _require_training_data_access() -> None:
    _deny_retired_saved_cohort_replay()


def _require_post_outcome_replay_gate() -> None:
    _deny_retired_saved_cohort_replay()


def _load_saved_targets_after_gate():
    _deny_retired_saved_cohort_replay()


def git_blob_sha1(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def sha256_bytes(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def load_module(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def load_frozen_modules(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def download_csv(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def build_training_frame(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def build_target_features(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def validate_targets(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def replay(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def assert_same_frozen_replay(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def restore_frozen_candidate_from_training_history(*args, **kwargs):
    _deny_retired_saved_cohort_replay()


def main() -> None:
    _deny_retired_saved_cohort_replay()


if __name__ == "__main__":
    main()

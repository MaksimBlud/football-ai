"""Single safe orchestration entry point for original V2 prospective evaluation.

The live caller cannot supply its own completed-fixture identities or gate
attestation. This wrapper obtains both from the read-only identity-only
Supabase gate, then delegates to the pure evaluator. The outcome loader remains
lazy and is invoked only by the evaluator after every frozen gate is satisfied.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from types import MappingProxyType
import re
from typing import Any, Callable, Iterable, Mapping

from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
import market_anchor_1x2_v2_prospective_evaluator as evaluator
from market_anchor_v2_source_rights import require_personal_research_inference_scope

from market_anchor_1x2_v2_completed_fixture_gate import read_completed_fixture_gate
from market_anchor_1x2_v2_prospective_evaluator import (
    _validate_completed_fixture_gate_attestation,
    evaluate_after_gate,
    evaluate_market_only_after_gate,
)


def evaluate_live_prospective_cohort(
    client: Any,
    forecast_rows: Iterable[Mapping[str, Any]],
    outcome_loader: Callable[[frozenset[tuple[str, str, str]]], Mapping[tuple[str, str, str], str]],
) -> dict[str, Any]:
    """Evaluate using a fresh identity-only gate read and a lazy outcome loader.

    This is the supported live orchestration path. It deliberately has no
    parameters for caller-supplied completed identities, attestation, cutoff,
    or preloaded outcomes. The gate reader samples its own current UTC clock
    and selects only match_date/home_team/away_team. The pure evaluator then
    enforces the 30 eligible completed primary-event gate and the separately
    pinned non-legacy incumbent requirement before it can invoke outcome_loader.
    """
    # This live runner is importable independently of the CLI. Enforce the
    # provider-rights boundary before its first Supabase identity read.
    require_personal_research_inference_scope()

    if not callable(outcome_loader):
        raise ValueError("outcome_loader must be a lazy callable, not preloaded outcomes")

    completed_identities, attestation = read_completed_fixture_gate(client)
    return evaluate_after_gate(
        forecast_rows,
        completed_identities,
        outcome_loader,
        completed_fixture_gate_attestation=attestation,
    )



_SOURCE_ARCHIVE_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def _expected_source_artifact_shas(forecast_rows: Iterable[Mapping[str, Any]]) -> dict[int, str]:
    expected: dict[int, str] = {}
    for row in forecast_rows:
        if not isinstance(row, Mapping):
            raise ValueError("market-only forecast rows must be mappings before source preflight")
        source_id = row.get("source_artifact_id")
        source_sha = row.get("source_archive_sha256")
        if type(source_id) is not int or source_id <= 0:
            raise ValueError("forecast source_artifact_id must be a positive integer")
        if not isinstance(source_sha, str) or _SOURCE_ARCHIVE_SHA256_RE.fullmatch(source_sha) is None:
            raise ValueError("forecast source_archive_sha256 must be a lowercase SHA-256")
        previous = expected.setdefault(source_id, source_sha)
        if previous != source_sha:
            raise ValueError("one source artifact ID cannot map to multiple forecast SHA-256 values")
    return expected


def _validate_source_preflight_sha_proof(
    expected: Mapping[int, str],
    proof: object,
) -> None:
    if not isinstance(proof, Mapping):
        raise ValueError("source preflight must return a verified artifact-ID-to-SHA-256 mapping")
    verified: dict[int, str] = {}
    for source_id, source_sha in proof.items():
        if type(source_id) is not int or source_id <= 0:
            raise ValueError("source preflight returned an invalid artifact ID")
        if not isinstance(source_sha, str) or _SOURCE_ARCHIVE_SHA256_RE.fullmatch(source_sha) is None:
            raise ValueError("source preflight returned an invalid artifact SHA-256")
        verified[source_id] = source_sha
    for source_id, source_sha in expected.items():
        if verified.get(source_id) != source_sha:
            raise ValueError("source preflight SHA proof does not match every forecast source artifact")


def evaluate_live_market_only_prospective_cohort(
    client: Any,
    forecast_rows: Iterable[Mapping[str, Any]],
    outcome_loader: Callable[[frozenset[tuple[str, str, str]]], Mapping[tuple[str, str, str], str]],
    *,
    preflight: Callable[[frozenset[tuple[str, str, str]], Mapping[str, Any], tuple[Mapping[str, Any], ...]], Mapping[int, str]],
) -> dict[str, Any]:
    """Run market-vs-shadow evaluation with mandatory source/archive SHA preflight.

    The required preflight receives the frozen identity set, a detached gate
    attestation, and immutable forecast-row copies. It must return the verified
    source artifact ID -> SHA-256 map. Every forecast row's source artifact ID
    and SHA must match that proof before the pure evaluator can reach its lazy
    outcome loader. The same identity set and original attestation are then
    passed to the evaluator; no second gate read is performed.
    """
    # This live runner is importable independently of the CLI. Enforce the
    # same provider-rights boundary before its first Supabase identity read.
    require_personal_research_inference_scope()

    if not callable(outcome_loader):
        raise ValueError("outcome_loader must be a lazy callable, not preloaded outcomes")
    if not callable(preflight):
        raise ValueError("preflight must be a callable source/archive verifier")

    rows = list(forecast_rows)
    expected_source_shas = _expected_source_artifact_shas(rows)
    completed_identities, attestation = read_completed_fixture_gate(client)
    frozen_identities = frozenset(completed_identities)
    _validate_completed_fixture_gate_attestation(attestation, frozen_identities)

    detached_attestation = MappingProxyType(deepcopy(dict(attestation)))
    immutable_rows = tuple(MappingProxyType(deepcopy(dict(row))) for row in rows)
    source_sha_proof = preflight(frozen_identities, detached_attestation, immutable_rows)
    _validate_source_preflight_sha_proof(expected_source_shas, source_sha_proof)

    return evaluate_market_only_after_gate(
        rows,
        frozen_identities,
        outcome_loader,
        completed_fixture_gate_attestation=attestation,
    )

# These aliases are the exact Serie A identity normalization used by the
# original V2 current-form source and the frozen prospective evaluator.
V2_ONLY_TEAM_ALIASES = {"Atalanta BC": "Atalanta"}


def _canonical_team(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("completed outcome team identity must be a non-empty string")
    value = value.strip()
    if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value):
        raise ValueError("completed outcome team identity contains control characters")
    configured = SERIE_A_RUNTIME_CONFIG.aliases.get(value, value)
    canonical = V2_ONLY_TEAM_ALIASES.get(configured, configured)
    if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in canonical):
        raise ValueError("completed outcome team identity contains control characters")
    return canonical


def _raw_team_aliases(canonical: str) -> list[str]:
    """Return only raw labels that normalize to one requested canonical team."""
    aliases = {canonical}
    for raw in SERIE_A_RUNTIME_CONFIG.aliases:
        if _canonical_team(raw) == canonical:
            aliases.add(raw)
    for raw in V2_ONLY_TEAM_ALIASES:
        if _canonical_team(raw) == canonical:
            aliases.add(raw)
    return sorted(aliases)


def _forecast_kickoff_lookup(
    forecast_rows: Iterable[Mapping[str, Any]],
) -> tuple[tuple[Mapping[str, Any], ...], dict[tuple[str, str, str], str]]:
    """Bind exact fixture identities to their frozen forecast kickoff timestamps."""
    rows = tuple(forecast_rows)
    kickoff_by_identity: dict[tuple[str, str, str], str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("forecast rows must be mappings before outcome provenance can be checked")
        identity = evaluator._identity(
            (row.get("match_date"), row.get("home_team"), row.get("away_team")),
            label="forecast identity",
        )
        kickoff = evaluator._utc(row.get("kickoff_utc"), "kickoff_utc")
        if kickoff.date().isoformat() != identity[0]:
            raise ValueError("forecast kickoff UTC date does not match canonical fixture match_date")
        kickoff_text = kickoff.isoformat().replace("+00:00", "Z")
        previous = kickoff_by_identity.get(identity)
        if previous is not None and previous != kickoff_text:
            raise ValueError("duplicate forecasts for one fixture disagree on kickoff_utc")
        kickoff_by_identity[identity] = kickoff_text
    return rows, kickoff_by_identity


def evaluate_live_market_only_from_supabase(
    client: Any,
    forecast_rows: Iterable[Mapping[str, Any]],
    *,
    observed_at_utc: str | None = None,
    preflight: Callable[[frozenset[tuple[str, str, str]], Mapping[str, Any], tuple[Mapping[str, Any], ...]], Mapping[int, str]],
    outcome_read_state: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Run market-vs-shadow evaluation with a gate-local exact-row outcome reader.

    The result-column query exists only as a nested lazy callback. There is no
    importable module-level outcome reader that can be called around the frozen
    30-identity / 30-eligible-forecast gate. The optional state sink is audit
    metadata only; it cannot initiate a read.
    """
    if not callable(preflight):
        raise ValueError("preflight must be a callable source/archive verifier")
    rows, kickoff_by_identity = _forecast_kickoff_lookup(forecast_rows)
    observed = observed_at_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    evaluator._utc(observed, "evaluation observed_at_utc")

    state = {"called": False}
    if outcome_read_state is not None:
        if not isinstance(outcome_read_state, dict):
            raise ValueError("outcome_read_state must be a mutable dictionary when supplied")
        outcome_read_state["called"] = False

    def load_exact_completed_outcomes_after_gate(
        identities: frozenset[tuple[str, str, str]],
    ) -> dict[tuple[str, str, str], str]:
        # This closure is passed only to the pure evaluator, which invokes it
        # after the frozen metadata-identity and eligible-forecast gates pass.
        state["called"] = True
        if outcome_read_state is not None:
            outcome_read_state["called"] = True

        from datetime import date

        if not isinstance(identities, frozenset) or not identities:
            raise ValueError("outcome loader requires a non-empty frozen set of exact fixture identities")
        outcomes: dict[tuple[str, str, str], str] = {}
        selected_columns = "match_date,home_team,away_team,result,persisted_at_utc"
        for identity in sorted(identities):
            if not isinstance(identity, tuple) or len(identity) != 3:
                raise ValueError("outcome loader received a malformed fixture identity")
            match_date, home, away = identity
            try:
                parsed_date = date.fromisoformat(match_date)
            except (TypeError, ValueError) as exc:
                raise ValueError("outcome loader fixture date must be canonical ISO form") from exc
            if parsed_date.isoformat() != match_date:
                raise ValueError("outcome loader fixture date must be canonical ISO form")
            canonical_home = _canonical_team(home)
            canonical_away = _canonical_team(away)
            if canonical_home != home or canonical_away != away or home == away:
                raise ValueError("outcome loader identities must already be canonical V2 fixture keys")
            kickoff_value = kickoff_by_identity.get(identity)
            if kickoff_value is None:
                raise ValueError("gated fixture has no matching frozen forecast kickoff timestamp")
            kickoff = evaluator._utc(kickoff_value, "kickoff_utc")
            if kickoff.date().isoformat() != match_date:
                raise ValueError("forecast kickoff UTC date does not match gated fixture identity")

            response = (
                client.table("league_finished_results")
                .select(selected_columns)
                .eq("league", SERIE_A_RUNTIME_CONFIG.identity.identifier)
                .eq("season", SERIE_A_RUNTIME_CONFIG.finished_results_source.season)
                .eq("match_date", match_date)
                .in_("home_team", _raw_team_aliases(home))
                .in_("away_team", _raw_team_aliases(away))
                .execute()
            )
            rows_for_fixture = getattr(response, "data", None)
            if not isinstance(rows_for_fixture, list) or not rows_for_fixture:
                raise ValueError(f"no completed outcome row found for gated fixture {identity!r}")
            labels: set[str] = set()
            for row in rows_for_fixture:
                if not isinstance(row, Mapping) or set(row) != {
                    "match_date", "home_team", "away_team", "result", "persisted_at_utc"
                }:
                    raise ValueError("outcome query returned fields outside the exact identity+result allowlist")
                raw_date = row["match_date"]
                if isinstance(raw_date, date):
                    raw_date = raw_date.isoformat()
                if raw_date != match_date:
                    raise ValueError("outcome query returned a different fixture date")
                raw_home = _canonical_team(row["home_team"])
                raw_away = _canonical_team(row["away_team"])
                if (raw_date, raw_home, raw_away) != identity:
                    raise ValueError("outcome query returned a different canonical fixture identity")
                persisted_at = evaluator._utc(row["persisted_at_utc"], "persisted_at_utc")
                if persisted_at <= kickoff:
                    raise ValueError("outcome persisted_at_utc must be strictly after kickoff_utc")
                if persisted_at > evaluator._utc(observed, "evaluation observed_at_utc"):
                    raise ValueError("outcome persisted_at_utc cannot be later than evaluation observation time")
                label = row["result"]
                if not isinstance(label, str) or label not in {"H", "D", "A"}:
                    raise ValueError("outcome query returned a malformed H/D/A result label")
                labels.add(label)
            if len(labels) != 1:
                raise ValueError("duplicate raw aliases disagree on the completed fixture result")
            outcomes[identity] = next(iter(labels))
        return outcomes

    try:
        return evaluate_live_market_only_prospective_cohort(
            client,
            rows,
            load_exact_completed_outcomes_after_gate,
            preflight=preflight,
        )
    finally:
        if outcome_read_state is not None:
            outcome_read_state["called"] = state["called"]


"""Single safe orchestration entry point for original V2 prospective evaluation.

The live caller cannot supply its own completed-fixture identities or gate
attestation. This wrapper obtains both from the read-only identity-only
Supabase gate, then delegates to the pure evaluator. The outcome loader remains
lazy and is invoked only by the evaluator after every frozen gate is satisfied.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping

from market_anchor_v2_artifact_privacy import require_private_repository_for_source_artifacts
from market_anchor_v2_source_rights import require_personal_research_inference_scope

from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
import market_anchor_1x2_v2_prospective_evaluator as evaluator

from market_anchor_1x2_v2_completed_fixture_gate import read_completed_fixture_gate
from market_anchor_1x2_v2_prospective_evaluator import (
    _validate_completed_fixture_gate_attestation,
    evaluate_after_gate,
    evaluate_market_only_after_gate,
)




def _now_utc() -> datetime:
    """Capture the real runtime clock; callers may not move outcome time into the future."""
    return datetime.now(timezone.utc)


def _require_v2_outcome_read_access() -> dict[str, Any]:
    """Require provider inference rights and private artifact storage before any result read."""
    require_personal_research_inference_scope()
    return require_private_repository_for_source_artifacts(
        os.environ.get("GITHUB_REPOSITORY", ""),
        os.environ.get("GITHUB_TOKEN", ""),
    )


def _source_requirements_manifest_sha256(
    source_requirements: Iterable[Mapping[str, Any]],
) -> str:
    """Digest the exact per-forecast source/archive/parent/quote provenance contract."""
    normalized = [dict(item) for item in source_requirements]
    normalized.sort(key=lambda item: tuple(item["fixture_identity"]))
    payload = json.dumps(
        normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _forecast_source_requirements(
    forecast_rows: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Bind each normalized forecast identity to its exact source and parent-run evidence."""
    requirements: dict[tuple[str, str, str], dict[str, Any]] = {}
    archive_metadata: dict[int, tuple[Any, ...]] = {}
    timestamp_fields = (
        "source_observed_at_utc",
        "source_archive_created_at_utc",
        "source_parent_run_completed_at_utc",
        "quote_time_utc",
        "forecast_captured_at_utc",
        "kickoff_utc",
    )
    archive_fields = (
        "source_archive_sha256",
        "source_parent_run_id",
        "source_parent_run_sha",
        "source_observed_at_utc",
        "source_archive_created_at_utc",
        "source_parent_run_completed_at_utc",
    )
    for row in forecast_rows:
        identity, _, _ = evaluator._validate_forecast(row)
        if identity in requirements:
            raise ValueError("duplicate canonical fixture identity in source preflight requirements")
        timestamps = {
            field: evaluator._utc(row[field], field).isoformat().replace("+00:00", "Z")
            for field in timestamp_fields
        }
        requirement = {
            "fixture_identity": identity,
            "event_id": row["event_id"].strip(),
            "source_artifact_id": row["source_artifact_id"],
            "source_archive_sha256": row["source_archive_sha256"],
            "source_parent_run_id": row["source_parent_run_id"],
            "source_parent_run_sha": row["source_parent_run_sha"],
            **timestamps,
        }
        archive_id = requirement["source_artifact_id"]
        archive_signature = tuple(requirement[field] for field in archive_fields)
        previous = archive_metadata.get(archive_id)
        if previous is not None and previous != archive_signature:
            raise ValueError("one source artifact ID maps to conflicting SHA or parent-run provenance")
        archive_metadata[archive_id] = archive_signature
        requirements[identity] = requirement
    return requirements


def _validate_source_preflight_attestation(
    value: Any,
    completed_fixture_gate_attestation: Mapping[str, Any],
    expected_source_requirements: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Require the independent preflight result to bind every exact eligible forecast source."""
    required_fields = {
        "verified",
        "source_archive_sha256",
        "source_parent_run_id",
        "source_parent_run_sha",
        "verified_source_archive_count",
        "verified_forecast_count",
        "forecast_source_manifest_sha256",
        "verified_forecast_identity_sha256",
        "gate_fixture_identity_count",
        "gate_fixture_identity_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != required_fields:
        raise PermissionError("source-before-quote preflight attestation has missing or unapproved fields")
    if value["verified"] is not True:
        raise PermissionError("source-before-quote preflight attestation is missing or unverified")

    sources = [dict(item) for item in expected_source_requirements]
    if not sources:
        raise PermissionError("source preflight cannot attest an empty eligible forecast source set")
    required_source_fields = {
        "fixture_identity",
        "event_id",
        "source_artifact_id",
        "source_archive_sha256",
        "source_parent_run_id",
        "source_parent_run_sha",
        "source_observed_at_utc",
        "source_archive_created_at_utc",
        "source_parent_run_completed_at_utc",
        "quote_time_utc",
        "forecast_captured_at_utc",
        "kickoff_utc",
    }
    expected_archive_sha: dict[str, str] = {}
    expected_parent_ids: dict[str, int] = {}
    expected_parent_shas: dict[str, str] = {}
    identities: set[tuple[str, str, str]] = set()
    archive_signatures: dict[str, tuple[Any, ...]] = {}
    for source in sources:
        if set(source) != required_source_fields:
            raise PermissionError("source preflight input contains missing or unapproved forecast provenance fields")
        identity_value = source["fixture_identity"]
        if not isinstance(identity_value, (tuple, list)) or len(identity_value) != 3:
            raise PermissionError("source preflight input has a malformed fixture identity")
        identity = evaluator._identity(tuple(identity_value), label="source preflight fixture identity")
        if identity in identities:
            raise PermissionError("source preflight input contains a duplicate fixture identity")
        identities.add(identity)
        artifact_id = source["source_artifact_id"]
        parent_id = source["source_parent_run_id"]
        if type(artifact_id) is not int or artifact_id <= 0 or type(parent_id) is not int or parent_id <= 0:
            raise PermissionError("source preflight input contains an invalid artifact or parent run ID")
        archive_key = str(artifact_id)
        archive_sha = source["source_archive_sha256"]
        parent_sha = source["source_parent_run_sha"]
        if not isinstance(archive_sha, str) or re.fullmatch(r"[0-9a-f]{64}", archive_sha) is None:
            raise PermissionError("source preflight input contains a malformed archive SHA-256")
        if not isinstance(parent_sha, str) or re.fullmatch(r"[0-9a-f]{40}", parent_sha) is None:
            raise PermissionError("source preflight input contains a malformed parent-run SHA")
        signature = (
            archive_sha,
            parent_id,
            parent_sha,
            source["source_observed_at_utc"],
            source["source_archive_created_at_utc"],
            source["source_parent_run_completed_at_utc"],
        )
        previous = archive_signatures.get(archive_key)
        if previous is not None and previous != signature:
            raise PermissionError("one source artifact ID maps to conflicting SHA or parent-run provenance")
        archive_signatures[archive_key] = signature
        expected_archive_sha[archive_key] = archive_sha
        expected_parent_ids[archive_key] = parent_id
        expected_parent_shas[archive_key] = parent_sha

        observed = evaluator._utc(source["source_observed_at_utc"], "source_observed_at_utc")
        archived = evaluator._utc(source["source_archive_created_at_utc"], "source_archive_created_at_utc")
        parent_completed = evaluator._utc(
            source["source_parent_run_completed_at_utc"], "source_parent_run_completed_at_utc"
        )
        quote = evaluator._utc(source["quote_time_utc"], "quote_time_utc")
        captured = evaluator._utc(source["forecast_captured_at_utc"], "forecast_captured_at_utc")
        kickoff = evaluator._utc(source["kickoff_utc"], "kickoff_utc")
        if not (observed <= archived <= parent_completed < quote <= captured < kickoff):
            raise PermissionError("source preflight input violates source-before-quote/kickoff ordering")
        if quote - observed > evaluator.MAX_SOURCE_AGE or captured - quote > evaluator.MAX_QUOTE_AGE:
            raise PermissionError("source preflight input violates the frozen source/quote age limits")

    if not isinstance(value["source_archive_sha256"], Mapping) or dict(value["source_archive_sha256"]) != expected_archive_sha:
        raise PermissionError("source preflight archive SHA map does not exactly match eligible forecast sources")
    if not isinstance(value["source_parent_run_id"], Mapping) or dict(value["source_parent_run_id"]) != expected_parent_ids:
        raise PermissionError("source preflight parent-run ID map does not exactly match eligible forecast sources")
    if not isinstance(value["source_parent_run_sha"], Mapping) or dict(value["source_parent_run_sha"]) != expected_parent_shas:
        raise PermissionError("source preflight parent-run SHA map does not exactly match eligible forecast sources")

    manifest_sha = _source_requirements_manifest_sha256(sources)
    identity_sha = evaluator._sha_fixture_set(identities)
    if type(value["verified_source_archive_count"]) is not int or value["verified_source_archive_count"] != len(expected_archive_sha):
        raise PermissionError("source preflight archive count does not match eligible forecast sources")
    if type(value["verified_forecast_count"]) is not int or value["verified_forecast_count"] != len(sources):
        raise PermissionError("source preflight forecast count does not match the eligible forecast source set")
    if value["forecast_source_manifest_sha256"] != manifest_sha:
        raise PermissionError("source preflight manifest SHA does not bind the exact eligible forecast sources")
    if value["verified_forecast_identity_sha256"] != identity_sha:
        raise PermissionError("source preflight fixture identity SHA does not match eligible forecasts")
    if type(value["gate_fixture_identity_count"]) is not int or value["gate_fixture_identity_count"] != completed_fixture_gate_attestation.get("completed_fixture_identity_count"):
        raise PermissionError("source preflight fixture count differs from the frozen identity gate")
    if value["gate_fixture_identity_sha256"] != completed_fixture_gate_attestation.get("completed_fixture_identity_sha256"):
        raise PermissionError("source preflight identity SHA differs from the frozen identity gate")
    return {
        "verified": True,
        "source_archive_sha256": expected_archive_sha,
        "source_parent_run_id": expected_parent_ids,
        "source_parent_run_sha": expected_parent_shas,
        "verified_source_archive_count": len(expected_archive_sha),
        "verified_forecast_count": len(sources),
        "forecast_source_manifest_sha256": manifest_sha,
        "verified_forecast_identity_sha256": identity_sha,
        "gate_fixture_identity_count": value["gate_fixture_identity_count"],
        "gate_fixture_identity_sha256": value["gate_fixture_identity_sha256"],
    }

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
    _require_v2_outcome_read_access()
    if not callable(outcome_loader):
        raise ValueError("outcome_loader must be a lazy callable, not preloaded outcomes")

    completed_identities, attestation = read_completed_fixture_gate(client)
    return evaluate_after_gate(
        forecast_rows,
        completed_identities,
        outcome_loader,
        completed_fixture_gate_attestation=attestation,
    )


def evaluate_live_market_only_prospective_cohort(
    client: Any,
    forecast_rows: Iterable[Mapping[str, Any]],
    outcome_loader: Callable[[frozenset[tuple[str, str, str]]], Mapping[tuple[str, str, str], str]],
    *,
    preflight: Callable[[frozenset[tuple[str, str, str]], Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run market-vs-shadow evaluation against one immutable identity-gate snapshot.

    The optional preflight receives only the frozen identity set and a detached
    attestation copy. It is intended for source/archive verification before
    evaluation. The exact same identity set and original attestation are then
    passed to the pure evaluator, avoiding a second Supabase gate read and any
    race between source-completeness verification and the outcome-read gate.
    It cannot receive target outcomes or alter the evaluator's attestation.
    """
    _require_v2_outcome_read_access()
    if not callable(outcome_loader):
        raise ValueError("outcome_loader must be a lazy callable, not preloaded outcomes")
    if not callable(preflight):
        raise ValueError("a verified source-before-quote preflight callback is required before live outcome evaluation")

    rows = tuple(forecast_rows)
    source_requirements_by_identity = _forecast_source_requirements(rows)
    completed_identities, attestation = read_completed_fixture_gate(client)
    frozen_identities = frozenset(completed_identities)
    _validate_completed_fixture_gate_attestation(attestation, frozen_identities)

    detached_attestation = MappingProxyType(deepcopy(dict(attestation)))
    expected_eligible_identities = frozenset(
        identity for identity in source_requirements_by_identity
        if identity in frozen_identities
    )

    def gated_outcome_loader(eligible_identities):
        if not isinstance(eligible_identities, frozenset) or len(eligible_identities) < evaluator.MIN_COMPLETED_ELIGIBLE_FORECASTS:
            raise PermissionError("outcome reader requires the frozen minimum of 30 eligible completed primary forecasts")
        if not eligible_identities.issubset(frozen_identities):
            raise PermissionError("eligible forecast identities fall outside the frozen completed-fixture gate")
        if eligible_identities != expected_eligible_identities:
            raise PermissionError("evaluator eligible identities differ from the exact forecast source manifest")
        # The evaluator invokes this loader only after it has verified at least
        # 30 unique eligible completed primary forecasts. Preflight receives the
        # exact per-forecast source IDs/SHAs, parent-run IDs/SHAs and ordered
        # observation/archive/parent/quote/capture/kickoff timestamps. It runs
        # after the 30-event gate and before the first target-outcome read.
        eligible_sources = tuple(
            source_requirements_by_identity[identity]
            for identity in sorted(eligible_identities)
        )
        preflight_inputs = tuple(
            MappingProxyType(dict(source)) for source in eligible_sources
        )
        source_preflight_attestation = _validate_source_preflight_attestation(
            preflight(preflight_inputs, detached_attestation),
            attestation,
            eligible_sources,
        )
        return outcome_loader(
            eligible_identities,
            completed_fixture_identities=frozen_identities,
            completed_fixture_gate_attestation=attestation,
            source_preflight_attestation=source_preflight_attestation,
            eligible_source_requirements=eligible_sources,
        )

    return evaluate_market_only_after_gate(
        rows,
        frozen_identities,
        gated_outcome_loader,
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


def _read_exact_completed_outcomes(
    client: Any,
    identities: frozenset[tuple[str, str, str]],
    kickoff_by_identity: Mapping[tuple[str, str, str], str],
    *,
    observed_at_utc: str,
    completed_fixture_identities: frozenset[tuple[str, str, str]],
    completed_fixture_gate_attestation: Mapping[str, Any],
    source_preflight_attestation: Mapping[str, Any],
    eligible_source_requirements: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, str, str], str]:
    """Read H/D/A labels for exact gated identities, never scores or extra fixtures.

    This function is intended only as the lazy callback passed to the market-only
    evaluator. Its caller must not invoke it before the evaluator opens the
    30-eligible-completed-prospective-forecast gate.
    """
    from datetime import date

    _require_v2_outcome_read_access()
    if not isinstance(identities, frozenset) or len(identities) < evaluator.MIN_COMPLETED_ELIGIBLE_FORECASTS:
        raise PermissionError("outcome reader requires at least 30 eligible completed primary forecasts")
    if not isinstance(completed_fixture_identities, frozenset) or not completed_fixture_identities:
        raise PermissionError("outcome reader requires the frozen completed-fixture identity set")
    if not identities.issubset(completed_fixture_identities):
        raise PermissionError("outcome reader identities fall outside the frozen completed-fixture gate")
    _validate_completed_fixture_gate_attestation(completed_fixture_gate_attestation, completed_fixture_identities)
    _validate_source_preflight_attestation(
        source_preflight_attestation,
        completed_fixture_gate_attestation,
        eligible_source_requirements,
    )
    expected_source_identities = {
        tuple(source["fixture_identity"]) for source in eligible_source_requirements
    }
    if expected_source_identities != set(identities):
        raise PermissionError("outcome reader source manifest does not match the exact gated forecast identities")
    if not isinstance(kickoff_by_identity, Mapping) or set(kickoff_by_identity) != set(identities):
        raise PermissionError("outcome reader kickoff map must exactly match the gated forecast identities")
    if not isinstance(kickoff_by_identity, Mapping):
        raise ValueError("outcome loader requires forecast-bound kickoff timestamps")
    observed_at = evaluator._utc(observed_at_utc, "evaluation observed_at_utc")
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
        rows = getattr(response, "data", None)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"no completed outcome row found for gated fixture {identity!r}")
        labels: set[str] = set()
        for row in rows:
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
            if persisted_at > observed_at:
                raise ValueError("outcome persisted_at_utc cannot be later than evaluation observation time")
            label = row["result"]
            if not isinstance(label, str) or label not in {"H", "D", "A"}:
                raise ValueError("outcome query returned a malformed H/D/A result label")
            labels.add(label)
        if len(labels) != 1:
            raise ValueError("duplicate raw aliases disagree on the completed fixture result")
        outcomes[identity] = next(iter(labels))
    return outcomes


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
    preflight: Callable[[frozenset[tuple[str, str, str]], Mapping[str, Any]], Mapping[str, Any]] | None = None,
    observed_at_utc: str | None = None,
) -> dict[str, Any]:
    """Run market-vs-shadow evaluation with an internally lazy, exact-row outcome reader.

    The only Supabase read before the frozen gate is the identity-only reader
    used by evaluate_live_market_only_prospective_cohort. The result-column
    query is encapsulated in a callback and is invoked only after 30 eligible
    completed prospective forecasts pass the evaluator gate.
    """
    _require_v2_outcome_read_access()
    if not callable(preflight):
        raise ValueError("a verified source-before-quote preflight callback is required before live outcome evaluation")
    rows, kickoff_by_identity = _forecast_kickoff_lookup(forecast_rows)
    clock = _now_utc()
    if not isinstance(clock, datetime) or clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("system evaluation clock must have a real UTC offset")
    clock = clock.astimezone(timezone.utc)
    observed_time = clock if observed_at_utc is None else evaluator._utc(observed_at_utc, "evaluation observed_at_utc")
    if observed_time > clock:
        raise ValueError("evaluation observed_at_utc cannot be later than the actual current UTC clock")
    observed = observed_time.isoformat().replace("+00:00", "Z")
    return evaluate_live_market_only_prospective_cohort(
        client,
        rows,
        lambda identities, **gate: _read_exact_completed_outcomes(
            client, identities, kickoff_by_identity, observed_at_utc=observed, **gate
        ),
        preflight=preflight,
    )


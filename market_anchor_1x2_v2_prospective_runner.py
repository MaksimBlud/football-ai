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
from market_anchor_1x2_v2_forward_artifact_adapter import select_first_eligible_forecasts
import market_anchor_1x2_v2_prospective_evaluator as evaluator
from market_anchor_v2_source_rights import require_personal_research_inference_scope
from market_anchor_v2_artifact_privacy import require_private_repository_for_source_artifacts

from market_anchor_1x2_v2_completed_fixture_gate import read_completed_fixture_gate
from market_anchor_1x2_v2_prospective_evaluator import (
    _validate_completed_fixture_gate_attestation,
    evaluate_after_gate,
    evaluate_market_only_after_gate,
)


def _require_live_research_access(token: str) -> None:
    """Enforce rights and private storage before any live identity/source read."""
    require_personal_research_inference_scope()
    if not isinstance(token, str) or not token.strip():
        raise PermissionError("GITHUB_TOKEN is required for live source verification")
    require_private_repository_for_source_artifacts(token=token)


def _snapshot_source_candidates(source_candidates: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], tuple[Mapping[str, Any], ...]]:
    """Detach selected forward rows and their embedded source ZIP provenance."""
    rows: list[dict[str, Any]] = []
    snapshots: list[Mapping[str, Any]] = []
    for candidate in source_candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError("source candidates must be mappings")
        row, provenance = candidate.get("row"), candidate.get("provenance")
        if not isinstance(row, Mapping) or not isinstance(provenance, Mapping):
            raise ValueError("each source candidate must contain row and provenance mappings")
        row_copy, provenance_copy = deepcopy(dict(row)), deepcopy(dict(provenance))
        rows.append(row_copy)
        snapshots.append(MappingProxyType({
            "row": MappingProxyType(row_copy),
            "provenance": MappingProxyType(provenance_copy),
        }))
    return rows, tuple(snapshots)


def _verify_source_candidates(candidates: tuple[Mapping[str, Any], ...], *, token: str,
                              current_gate_identities: frozenset[tuple[str, str, str]],
                              gate_attestation: Mapping[str, Any]) -> Mapping[int, str]:
    """Invoke the concrete GitHub artifact/ZIP/parent-run verifier, never a caller callback."""
    from market_anchor_1x2_v2_prospective_evaluation import verify_source_artifacts_for_candidates
    return verify_source_artifacts_for_candidates(
        list(candidates), token=token, current_gate_identities=set(current_gate_identities)
    )


_SOURCE_ARCHIVE_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def _expected_source_artifact_shas(forecast_rows: Iterable[Mapping[str, Any]]) -> dict[int, str]:
    expected: dict[int, str] = {}
    for row in forecast_rows:
        if not isinstance(row, Mapping):
            raise ValueError("market-only forecast rows must be mappings before source verification")
        source_id, source_sha = row.get("source_artifact_id"), row.get("source_archive_sha256")
        if type(source_id) is not int or source_id <= 0:
            raise ValueError("forecast source_artifact_id must be a positive integer")
        if not isinstance(source_sha, str) or _SOURCE_ARCHIVE_SHA256_RE.fullmatch(source_sha) is None:
            raise ValueError("forecast source_archive_sha256 must be a lowercase SHA-256")
        previous = expected.setdefault(source_id, source_sha)
        if previous != source_sha:
            raise ValueError("one source artifact ID cannot map to multiple forecast SHA-256 values")
    return expected


def _validate_source_preflight_sha_proof(expected: Mapping[int, str], proof: object) -> dict[int, str]:
    if not isinstance(proof, Mapping):
        raise ValueError("internal source verifier must return an artifact-ID-to-SHA-256 mapping")
    verified: dict[int, str] = {}
    for source_id, source_sha in proof.items():
        if type(source_id) is not int or source_id <= 0:
            raise ValueError("source verifier returned an invalid artifact ID")
        if not isinstance(source_sha, str) or _SOURCE_ARCHIVE_SHA256_RE.fullmatch(source_sha) is None:
            raise ValueError("source verifier returned an invalid artifact SHA-256")
        verified[source_id] = source_sha
    if set(verified) != set(expected):
        raise ValueError("source verifier must cover exactly the selected source artifacts")
    for source_id, source_sha in expected.items():
        if verified.get(source_id) != source_sha:
            raise ValueError("source verifier SHA proof does not match every selected forecast source artifact")
    return verified


def _attach_source_sha_proof(report: Mapping[str, Any], verified: Mapping[int, str]) -> dict[str, Any]:
    result = dict(report)
    result["source_archives_reverified"] = len(verified)
    result["source_archive_sha256"] = {
        str(source_id): source_sha for source_id, source_sha in sorted(verified.items())
    }
    return result


def _select_verified_candidates(
    immutable_candidates: tuple[Mapping[str, Any], ...],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply the frozen earliest-eligible policy only after source verification."""
    selection_input = [
        {"row": dict(item["row"]), "provenance": dict(item["provenance"])}
        for item in immutable_candidates
    ]
    return select_first_eligible_forecasts(selection_input)


def evaluate_live_prospective_cohort(
    client: Any,
    source_candidates: Iterable[Mapping[str, Any]],
    outcome_loader: Callable[[frozenset[tuple[str, str, str]]], Mapping[tuple[str, str, str], str]],
    *,
    token: str,
) -> dict[str, Any]:
    """Evaluate only after rights, private storage, source ZIP and frozen gates.

    The caller cannot provide a preflight callback or SHA map. Every captured
    source candidate is verified before the frozen selection policy is applied.
    """
    _require_live_research_access(token)
    if not callable(outcome_loader):
        raise ValueError("outcome_loader must be a lazy callable, not preloaded outcomes")
    rows, immutable_candidates = _snapshot_source_candidates(source_candidates)
    expected_source_shas = _expected_source_artifact_shas(rows)
    completed_identities, attestation = read_completed_fixture_gate(client)
    frozen_identities = frozenset(completed_identities)
    _validate_completed_fixture_gate_attestation(attestation, frozen_identities)
    detached_attestation = MappingProxyType(deepcopy(dict(attestation)))
    proof = _verify_source_candidates(
        immutable_candidates, token=token, current_gate_identities=frozen_identities,
        gate_attestation=detached_attestation,
    )
    verified = _validate_source_preflight_sha_proof(expected_source_shas, proof)
    selected, selection = _select_verified_candidates(immutable_candidates)
    selected_rows = [dict(item["row"]) for item in selected]
    report = evaluate_after_gate(
        selected_rows, frozen_identities, outcome_loader,
        completed_fixture_gate_attestation=attestation,
    )
    result = _attach_source_sha_proof(report, verified)
    result["forecast_candidate_count"] = len(rows)
    result["selected_unique_fixture_forecasts"] = len(selected)
    result["selection"] = selection
    return result


def evaluate_live_market_only_prospective_cohort(
    client: Any,
    source_candidates: Iterable[Mapping[str, Any]],
    outcome_loader: Callable[[frozenset[tuple[str, str, str]]], Mapping[tuple[str, str, str], str]],
    *,
    token: str,
) -> dict[str, Any]:
    """Run market-vs-shadow evaluation with runner-owned source verification.

    No caller-supplied callback or self-reported SHA map is accepted. All
    captured source candidates are checked against GitHub artifact metadata,
    embedded ZIP bytes, source parent workflow and quote-time order before the
    frozen earliest-eligible selection policy or outcome loader can run.
    """
    _require_live_research_access(token)
    if not callable(outcome_loader):
        raise ValueError("outcome_loader must be a lazy callable, not preloaded outcomes")
    rows, immutable_candidates = _snapshot_source_candidates(source_candidates)
    expected_source_shas = _expected_source_artifact_shas(rows)
    completed_identities, attestation = read_completed_fixture_gate(client)
    frozen_identities = frozenset(completed_identities)
    _validate_completed_fixture_gate_attestation(attestation, frozen_identities)
    detached_attestation = MappingProxyType(deepcopy(dict(attestation)))
    proof = _verify_source_candidates(
        immutable_candidates, token=token, current_gate_identities=frozen_identities,
        gate_attestation=detached_attestation,
    )
    verified = _validate_source_preflight_sha_proof(expected_source_shas, proof)
    selected, selection = _select_verified_candidates(immutable_candidates)
    selected_rows = [dict(item["row"]) for item in selected]
    report = evaluate_market_only_after_gate(
        selected_rows, frozen_identities, outcome_loader,
        completed_fixture_gate_attestation=attestation,
    )
    result = _attach_source_sha_proof(report, verified)
    result["forecast_candidate_count"] = len(rows)
    result["selected_unique_fixture_forecasts"] = len(selected)
    result["selection"] = selection
    return result


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
    source_candidates: Iterable[Mapping[str, Any]],
    *,
    token: str,
    observed_at_utc: str | None = None,
    outcome_read_state: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Run market-vs-shadow evaluation with a gate-local exact-row outcome reader.

    The result-column query exists only as a nested lazy callback. There is no
    importable module-level outcome reader that can be called around the frozen
    30-identity / 30-eligible-forecast gate. The optional state sink is audit
    metadata only; it cannot initiate a read.
    """
    _require_live_research_access(token)
    state = {"called": False}
    if outcome_read_state is not None:
        if not isinstance(outcome_read_state, dict):
            raise ValueError("outcome_read_state must be a mutable dictionary when supplied")
        outcome_read_state["called"] = False

    actual_now = datetime.now(timezone.utc)
    if observed_at_utc is None:
        observed_time = actual_now
    else:
        observed_time = evaluator._utc(observed_at_utc, "evaluation observed_at_utc")
        if observed_time > actual_now:
            raise ValueError("evaluation observed_at_utc cannot be later than the actual current UTC clock")
    observed = observed_time.isoformat().replace("+00:00", "Z")

    rows, candidate_snapshot = _snapshot_source_candidates(source_candidates)
    rows, kickoff_by_identity = _forecast_kickoff_lookup(rows)

    def load_exact_completed_outcomes_after_gate(
        identities: frozenset[tuple[str, str, str]],
    ) -> dict[tuple[str, str, str], str]:
        # This closure is passed only to the pure evaluator, which invokes it
        # after the frozen metadata-identity and eligible-forecast gates pass.
        state["called"] = True
        if outcome_read_state is not None:
            outcome_read_state["called"] = True

        from datetime import date

        if (
            not isinstance(identities, frozenset)
            or len(identities) < evaluator.MIN_COMPLETED_ELIGIBLE_FORECASTS
        ):
            raise ValueError("outcome loader requires the frozen 30-eligible-completed-forecast gate")
        if not identities.issubset(kickoff_by_identity):
            raise PermissionError("outcome loader identities are outside the frozen forecast candidate set")
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
            candidate_snapshot,
            load_exact_completed_outcomes_after_gate,
            token=token,
        )
    finally:
        if outcome_read_state is not None:
            outcome_read_state["called"] = state["called"]


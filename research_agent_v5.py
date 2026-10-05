"""Deterministic no-API Research Agent V5.

The worker is an explicit state machine. It uses repository code/data and public
zero-cost transports only; it never needs an LLM provider key.
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
from pathlib import Path
from typing import Any


class LocalResearchError(RuntimeError):
    pass


RECIPE_REGISTRY = Path("research/v5_recipe_registry.json")
FAMILY_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
SAFE_RECIPE_CONTRACT = {
    "model_api": False,
    "paid_odds_api": False,
    "supabase_writes": False,
    "production_operations": False,
    "automatic_promotion": False,
}

EVALUATOR_MODULE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
RESULT_PATH_RE = re.compile(r"^[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*$")


def _validate_pipeline_recipe(family: str, recipe: dict[str, Any]) -> None:
    pipeline = recipe.get("pipeline")
    if not isinstance(pipeline, dict):
        raise LocalResearchError(f"V5 pipeline recipe {family} requires pipeline config")
    module = str(pipeline.get("evaluator_module", ""))
    if not EVALUATOR_MODULE_RE.fullmatch(module):
        raise LocalResearchError(
            f"V5 pipeline recipe {family} has invalid evaluator_module {module!r}"
        )
    preregistration = pipeline.get("preregistration_markdown")
    if not isinstance(preregistration, str) or not preregistration.strip():
        raise LocalResearchError(
            f"V5 pipeline recipe {family} requires preregistration_markdown"
        )
    if len(preregistration) > 20000:
        raise LocalResearchError(
            f"V5 pipeline recipe {family} preregistration_markdown is too large"
        )
    decision_path = str(pipeline.get("decision_path", ""))
    if not RESULT_PATH_RE.fullmatch(decision_path):
        raise LocalResearchError(
            f"V5 pipeline recipe {family} has invalid decision_path"
        )
    summary_path = pipeline.get("summary_path")
    if summary_path is not None and not RESULT_PATH_RE.fullmatch(str(summary_path)):
        raise LocalResearchError(
            f"V5 pipeline recipe {family} has invalid summary_path"
        )
    fields = pipeline.get("report_fields", [])
    if not isinstance(fields, list) or any(
        not isinstance(path, str) or not RESULT_PATH_RE.fullmatch(path)
        for path in fields
    ):
        raise LocalResearchError(
            f"V5 pipeline recipe {family} has invalid report_fields"
        )
    title = pipeline.get("report_title")
    if title is not None and (not isinstance(title, str) or not title.strip()):
        raise LocalResearchError(
            f"V5 pipeline recipe {family} has invalid report_title"
        )


def load_recipe_registry(root: Path) -> dict[str, Any]:
    path = root / RECIPE_REGISTRY
    payload = _load(path)
    if payload.get("schema_version") != 1:
        raise LocalResearchError("unsupported V5 recipe registry schema")
    if payload.get("engine") != "V5_DETERMINISTIC_NO_API":
        raise LocalResearchError("V5 recipe registry engine mismatch")
    recipes = payload.get("recipes")
    if not isinstance(recipes, list) or not recipes:
        raise LocalResearchError("V5 recipe registry must contain recipes")

    seen: set[str] = set()
    for recipe in recipes:
        if not isinstance(recipe, dict):
            raise LocalResearchError("V5 recipe entry must be an object")
        family = str(recipe.get("hypothesis_family", ""))
        handler = str(recipe.get("handler", ""))
        max_iterations = recipe.get("max_iterations")
        if not FAMILY_RE.fullmatch(family):
            raise LocalResearchError(f"invalid V5 hypothesis_family: {family!r}")
        if family in seen:
            raise LocalResearchError(f"duplicate V5 hypothesis_family: {family}")
        seen.add(family)
        if handler not in BUILTIN_HANDLERS:
            raise LocalResearchError(
                f"V5 recipe {family} references unknown handler {handler!r}"
            )
        if handler == "pipeline":
            _validate_pipeline_recipe(family, recipe)
        if not isinstance(max_iterations, int) or not 1 <= max_iterations <= 20:
            raise LocalResearchError(
                f"V5 recipe {family} max_iterations must be in 1..20"
            )
        if recipe.get("safety") != SAFE_RECIPE_CONTRACT:
            raise LocalResearchError(f"V5 recipe {family} safety contract mismatch")
    return payload


def recipe_for_family(root: Path, hypothesis_family: str) -> dict[str, Any] | None:
    family = hypothesis_family.strip()
    for recipe in load_recipe_registry(root)["recipes"]:
        if recipe["hypothesis_family"] == family:
            return recipe
    return None


def supports_family(root: Path, hypothesis_family: str) -> bool:
    return recipe_for_family(root, hypothesis_family) is not None


def max_iterations_for_family(root: Path, hypothesis_family: str) -> int:
    recipe = recipe_for_family(root, hypothesis_family)
    if recipe is None:
        raise LocalResearchError(
            f"no V5 deterministic recipe for {hypothesis_family!r}"
        )
    return int(recipe["max_iterations"])


def _issue_root(root: Path, issue: int) -> Path:
    return root / "research" / "agent_runs" / f"issue_{issue}"


def _docs_root(root: Path, issue: int) -> Path:
    return root / "docs" / "agent_runs" / f"issue_{issue}"


def _text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise LocalResearchError(f"missing required artifact: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LocalResearchError(f"expected object: {path}")
    return value


def _progress(root: Path, issue: int, finding: str, evidence: str, next_action: str | None = None) -> None:
    path = _issue_root(root, issue) / "PROGRESS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "## Deterministic V5 checkpoint",
        "",
        f"**Finding:** {finding}",
        "",
        f"**Evidence:** {evidence}",
    ]
    if next_action:
        lines += ["", f"**Next action:** {next_action}"]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n\n")


def _result_value(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise LocalResearchError(
                f"result path {dotted_path!r} is missing at {part!r}"
            )
        current = current[part]
    return current


def _render_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _state(root: Path, issue: int, status: str, summary: str, next_step: str | None = None) -> None:
    status = status.upper()
    if status == "CONTINUE" and not next_step:
        raise LocalResearchError("CONTINUE requires next_step")
    _json(
        _issue_root(root, issue) / "STATE.json",
        {
            "status": status,
            "summary": summary,
            "next_step": next_step,
            "blocker": None,
            "engine": "V5_DETERMINISTIC_NO_API",
        },
    )


def _pipeline(root: Path, issue: int, recipe: dict[str, Any]) -> None:
    pipeline = recipe["pipeline"]
    box = _issue_root(root, issue)
    prereg_path = box / "PREREGISTRATION.md"
    result_path = box / "RESULT.json"
    family = recipe["hypothesis_family"]
    title = pipeline.get("report_title") or family

    if not prereg_path.is_file():
        prereg = str(pipeline["preregistration_markdown"]).strip()
        _text(prereg_path, prereg)
        _progress(
            root,
            issue,
            f"Frozen deterministic protocol written for {family}.",
            "PREREGISTRATION.md was persisted before evaluator execution.",
            "Run the registered deterministic evaluator.",
        )
        _state(
            root,
            issue,
            "CONTINUE",
            f"Frozen deterministic protocol written for {family}.",
            "Run the registered deterministic evaluator.",
        )
        return

    if not result_path.is_file():
        module_name = str(pipeline["evaluator_module"])
        module = importlib.import_module(module_name)
        evaluator = getattr(module, "evaluate", None)
        if not callable(evaluator):
            raise LocalResearchError(
                f"registered evaluator {module_name}.evaluate is not callable"
            )
        report = evaluator()
        if not isinstance(report, dict):
            raise LocalResearchError(
                f"registered evaluator {module_name}.evaluate must return a dict"
            )
        decision = _result_value(report, str(pipeline["decision_path"]))
        _json(result_path, report)
        _progress(
            root,
            issue,
            f"Registered deterministic evaluator completed for {family}.",
            f"RESULT.json decision={_render_value(decision)}.",
            "Render the final report from the frozen deterministic result.",
        )
        _state(
            root,
            issue,
            "CONTINUE",
            f"Deterministic evaluation complete: {_render_value(decision)}.",
            "Render final report and close the research direction.",
        )
        return

    report = _load(result_path)
    decision = _result_value(report, str(pipeline["decision_path"]))
    summary = ""
    summary_path = pipeline.get("summary_path")
    if summary_path:
        summary = _render_value(_result_value(report, str(summary_path)))

    field_lines: list[str] = []
    for dotted_path in pipeline.get("report_fields", []):
        field_lines.append(
            f"- `{dotted_path}`: {_render_value(_result_value(report, dotted_path))}"
        )
    fields_md = "\n".join(field_lines) if field_lines else "- See RESULT.json."

    final = f"""# Research V5 final report — Issue #{issue}

## Вывод простым языком

Детерминированное исследование **{title}** завершено без внешней LLM/API-квоты.

Финальное решение: **{_render_value(decision)}**.

{summary}

## Technical appendix

Full reproducible result:
`research/agent_runs/issue_{issue}/RESULT.json`.

Key registered result fields:
{fields_md}

Safety contract: model API = false; paid Odds API = false; Supabase writes = false;
production operations = false; automatic promotion = false.
"""
    _text(_docs_root(root, issue) / "FINAL_REPORT.md", final)
    _state(
        root,
        issue,
        "DONE",
        f"Deterministic pipeline completed: {_render_value(decision)}.",
    )


def _replication(root: Path, issue: int) -> None:
    canonical_path = root / "experiments" / "cross_market_lead_lag_replication_v2_report.json"
    canonical = _load(canonical_path)
    result = canonical.get("result") or {}
    safety = canonical.get("safety") or {}
    expected = {
        "match_outcomes_used": False,
        "opened_2026_27_data_used": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_model_operations": 0,
        "production_promotion": False,
    }
    if any(safety.get(k) != v for k, v in expected.items()):
        raise LocalResearchError("canonical replication safety contract mismatch")
    if result.get("decision") != "LEAD_LAG_REPLICATION_NOT_SUPPORTED":
        raise LocalResearchError("unexpected frozen replication decision")

    validation = result["validation"]
    test = result["test"]
    proof = {
        "engine": "V5_DETERMINISTIC_NO_API",
        "canonical_source": str(canonical_path.relative_to(root)),
        "formal_decision": result["decision"],
        "product_decision": "CLOSE_DIRECTION",
        "paid_collection_justified": False,
        "validation": {
            "rows": validation["rows"],
            "mean_alignment_dot": validation["mean_alignment_dot"],
            "positive_leagues": validation["positive_mean_alignment_leagues"],
            "permutation_p": validation["permutation"]["one_sided_p"],
            "bootstrap_ci95": [
                validation["bootstrap"]["ci95_low"],
                validation["bootstrap"]["ci95_high"],
            ],
            "admissible": validation["admissible"],
        },
        "oot_2025_26": {
            "rows": test["rows"],
            "mean_alignment_dot": test["mean_alignment_dot"],
            "positive_leagues": test["positive_mean_alignment_leagues"],
            "permutation_p": test["permutation"]["one_sided_p"],
            "bootstrap_ci95": [
                test["bootstrap"]["ci95_low"],
                test["bootstrap"]["ci95_high"],
            ],
            "gate": test["gate"],
        },
        "safety": expected,
    }
    _json(_issue_root(root, issue) / "CANONICAL_RESULT.json", proof)
    _progress(
        root,
        issue,
        "Canonical Bundesliga/Ligue 1 independent replication is complete and formally negative.",
        (
            f"Validation admissible={validation['admissible']}; untouched OOT gate={test['gate']}; "
            "frozen combined decision=LEAD_LAG_REPLICATION_NOT_SUPPORTED."
        ),
        "Close the direction without paid intraday collection.",
    )
    _text(
        _docs_root(root, issue) / "FINAL_REPORT.md",
        f"""# Research V5 final report — Issue #{issue}

## Вывод простым языком

Независимая репликация на Bundesliga и Ligue 1 уже выполнена canonical zero-cost кодом.
По заранее замороженному правилу она **не подтвердила** lead-lag: validation 2024/25
не прошёл gate. Положительный OOT 2025/26 не может задним числом спасти validation.

Финальное решение: **CLOSE_DIRECTION**. Не запускать платный intraday collector, не
использовать сигнал в betting/production и не ослаблять frozen gates.

## Technical appendix

Canonical source: `experiments/cross_market_lead_lag_replication_v2_report.json`.

Validation 2024/25: rows={validation['rows']}, mean={validation['mean_alignment_dot']},
positive leagues={validation['positive_mean_alignment_leagues']}/2,
permutation p={validation['permutation']['one_sided_p']},
bootstrap 95% CI=[{validation['bootstrap']['ci95_low']}, {validation['bootstrap']['ci95_high']}],
admissible={validation['admissible']}.

OOT 2025/26: rows={test['rows']}, mean={test['mean_alignment_dot']},
positive leagues={test['positive_mean_alignment_leagues']}/2,
permutation p={test['permutation']['one_sided_p']},
bootstrap 95% CI=[{test['bootstrap']['ci95_low']}, {test['bootstrap']['ci95_high']}],
gate={test['gate']}.

Frozen decision: **{result['decision']}**. Result: **NO_BET**.
No outcomes, no 2026/27 outcomes, no paid API, no Supabase writes, no production operation
or promotion.
""",
    )
    _state(root, issue, "DONE", "Independent replication is formally negative; CLOSE_DIRECTION.")


def _anomaly(root: Path, issue: int) -> None:
    box = _issue_root(root, issue)
    prereg = box / "PREREGISTRATION.md"
    result_path = box / "RESULT.json"
    if not prereg.is_file():
        _text(
            prereg,
            f"""# Issue #{issue} — frozen 2024/25 anomaly audit

Status: **PREREGISTERED / POST-HOC / OUTCOME-FREE / NO_BET**.

Before calculating comparisons, freeze these diagnostic families:
1. source coverage/schema and reconstruction eligibility;
2. exact half-goal AH-line composition;
3. opening/closing 1X2, O/U 2.5 and AH overround;
4. gap_open_tv, open_to_close_move_tv, gap_reduction_tv, lead/move norms, AH residual;
5. league/sample composition and leave-one-league-out decomposition.

Compare 2024/25 only with 2023/24, 2025/26 and pooled 2019/20–2023/24.
Do not change alignment_dot, choose components/leagues/thresholds, use outcomes, use
2026/27, paid APIs, Supabase or production.
""",
        )
        _progress(root, issue, "Diagnostic contract frozen before new comparisons.", "PREREGISTRATION.md fixes all five required families.", "Run deterministic anomaly audit.")
        _state(root, issue, "CONTINUE", "Frozen anomaly protocol written.", "Run deterministic 2024/25 source/market anomaly audit.")
        return

    if not result_path.is_file():
        from cross_market_lead_lag_anomaly_audit_v1 import evaluate
        report = evaluate()
        _json(result_path, report)
        _progress(
            root,
            issue,
            "All frozen anomaly diagnostic families were computed by deterministic Python.",
            f"RESULT.json diagnostic_label={report['diagnostic_label']}; rows={report['rows']}.",
            "Render the final report.",
        )
        _state(root, issue, "CONTINUE", f"Anomaly audit complete: {report['diagnostic_label']}.", "Render final report and close.")
        return

    report = _load(result_path)
    label = report["diagnostic_label"]
    plain = (report.get("summary") or {}).get("plain_language", "See RESULT.json for deterministic details.")
    _text(
        _docs_root(root, issue) / "FINAL_REPORT.md",
        f"""# Research V5 final report — Issue #{issue}

## Вывод простым языком

Диагностика 2024/25 выполнена полностью deterministic Python без LLM/API.
Итог: **{label}**.

{plain}

Formal V1/V2 decisions remain unchanged. Это не betting signal и не разрешение на
production/promotion или paid collection.

## Technical appendix

Result: `research/agent_runs/issue_{issue}/RESULT.json`.
Rows: {report['rows']}. Diagnostic families: coverage/schema, AH composition, overround,
structural magnitudes, league/sample composition. Outcome-free; no 2026/27; no paid API;
no Supabase; no production operation.
""",
    )
    _state(root, issue, "DONE", f"2024/25 anomaly audit completed: {label}.")


def _kickoff(root: Path, issue: int) -> None:
    box = _issue_root(root, issue)
    prereg = box / "PREREGISTRATION.md"
    result_path = box / "RESULT.json"
    if not prereg.is_file():
        _text(
            prereg,
            f"""# Issue #{issue} — frozen kickoff/calendar O/U 2.5 protocol

Status: **PREREGISTERED / TEMPORAL OOS / RESEARCH ONLY**.

Leagues: EPL, La Liga, Serie A. No 2026/27.
Reference/train: through 2023/24; validation: 2024/25; untouched test: 2025/26.
Target: FTHG + FTAG > 2.5.
Baseline: league + devigged Bet365 O/U 2.5 probability.
Calendar extension: weekday, kickoff-hour sin/cos and frozen time-slot buckets.
Estimator: fixed regularized logistic regression.
Primary metric: log loss; Brier/AUC diagnostics.
Support requires lower calendar-model log loss in validation and OOT plus OOT paired
bootstrap 95% CI for calendar-minus-baseline log-loss delta entirely below zero.
No production model, paid API, Supabase or automatic promotion.
""",
        )
        _progress(root, issue, "Kickoff-calendar O/U 2.5 contract frozen before evaluation.", "Temporal splits, features, estimator and OOT uncertainty gate are fixed.", "Run deterministic OOS evaluation.")
        _state(root, issue, "CONTINUE", "Frozen kickoff-calendar OOS protocol written.", "Run deterministic kickoff-calendar O/U 2.5 evaluation.")
        return

    if not result_path.is_file():
        from kickoff_calendar_context_v1 import evaluate
        report = evaluate()
        _json(result_path, report)
        _progress(
            root,
            issue,
            "Kickoff time/weekday were evaluated with the frozen temporal OOS design.",
            f"decision={report['decision']}; validation_rows={report['validation']['rows']}; test_rows={report['test']['rows']}.",
            "Render the final report.",
        )
        _state(root, issue, "CONTINUE", f"Kickoff-calendar evaluation complete: {report['decision']}.", "Render final report and close.")
        return

    report = _load(result_path)
    validation, test = report["validation"], report["test"]
    _text(
        _docs_root(root, issue) / "FINAL_REPORT.md",
        f"""# Research V5 final report — Issue #{issue}

## Вывод простым языком

Исследование времени начала и дня недели завершено deterministic Python без внешней
LLM/API-квоты. Решение: **{report['decision']}**.

Validation calendar-minus-baseline log loss:
**{validation['calendar_minus_baseline_log_loss']}**.

OOT calendar-minus-baseline log loss:
**{test['calendar_minus_baseline_log_loss']}**,
paired-bootstrap 95% CI:
**[{test['bootstrap']['ci95_low']}, {test['bootstrap']['ci95_high']}]**.

## Technical appendix

Temporal split: <=2023/24 / 2024/25 / 2025/26.
Market baseline: devigged Bet365 O/U 2.5 + league.
Extension: weekday + kickoff cyclic features + frozen slot.
No paid API, Supabase, production model operation or promotion.
Full result: `research/agent_runs/issue_{issue}/RESULT.json`.
""",
    )
    _state(root, issue, "DONE", f"Kickoff-calendar OOS research completed: {report['decision']}.")


BUILTIN_HANDLERS = {
    "replication": _replication,
    "pipeline": _pipeline,
}


def run(root: Path, issue_number: int, hypothesis_family: str) -> None:
    recipe = recipe_for_family(root, hypothesis_family)
    if recipe is None:
        raise LocalResearchError(
            f"no V5 deterministic recipe for {hypothesis_family!r}"
        )
    handler_name = recipe["handler"]
    if handler_name == "pipeline":
        _pipeline(root, issue_number, recipe)
    else:
        BUILTIN_HANDLERS[handler_name](root, issue_number)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-number", type=int)
    parser.add_argument("--hypothesis-family")
    parser.add_argument("--supports-family")
    parser.add_argument("--max-iterations")
    parser.add_argument("--list-families", action="store_true")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    if args.list_families:
        for recipe in load_recipe_registry(args.root)["recipes"]:
            print(recipe["hypothesis_family"])
        return
    if args.supports_family is not None:
        raise SystemExit(0 if supports_family(args.root, args.supports_family) else 1)
    if args.max_iterations is not None:
        print(max_iterations_for_family(args.root, args.max_iterations))
        return
    if args.issue_number is None or not args.hypothesis_family:
        parser.error("--issue-number and --hypothesis-family are required for a research pass")
    run(args.root, args.issue_number, args.hypothesis_family)


if __name__ == "__main__":
    main()

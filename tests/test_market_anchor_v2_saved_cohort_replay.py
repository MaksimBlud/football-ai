"""Outcome-blind static tests for the retired saved-cohort replay/refit path."""
import ast
from pathlib import Path


SCRIPT = Path("market_anchor_v2_saved_cohort_replay.py")
ENTRYPOINTS = (
    "load_module",
    "load_frozen_modules",
    "download_csv",
    "build_training_frame",
    "build_target_features",
    "validate_targets",
    "replay",
    "assert_same_frozen_replay",
    "restore_frozen_candidate_from_training_history",
    "main",
)


def _functions():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _first_statement_after_docstring(node):
    body = list(node.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body.pop(0)
    return body[0] if body else None


def _first_call_name(node):
    statement = _first_statement_after_docstring(node)
    if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
        return None
    func = statement.value.func
    return func.id if isinstance(func, ast.Name) else None


def test_retirement_guard_is_an_unconditional_permission_error():
    guard = _functions()["_deny_retired_saved_cohort_replay"]
    statement = _first_statement_after_docstring(guard)
    assert isinstance(statement, ast.Raise)
    assert isinstance(statement.exc, ast.Call)
    assert isinstance(statement.exc.func, ast.Name)
    assert statement.exc.func.id == "PermissionError"


def test_every_saved_cohort_entrypoint_fails_before_input_or_io():
    functions = _functions()
    for name in ENTRYPOINTS:
        assert _first_call_name(functions[name]) == "_deny_retired_saved_cohort_replay"


def test_compatibility_gates_delegate_to_the_unconditional_retirement():
    functions = _functions()
    assert _first_call_name(functions["_require_training_data_access"]) == "_deny_retired_saved_cohort_replay"
    assert _first_call_name(functions["_require_post_outcome_replay_gate"]) == "_deny_retired_saved_cohort_replay"


def test_retired_target_cohort_is_not_embedded_at_module_scope():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    assignments = [
        node for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    assert not any(
        isinstance(target, ast.Name) and target.id == "TARGETS"
        for node in assignments
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
    )


def test_cli_is_retired_before_argument_parsing():
    assert _first_call_name(_functions()["main"]) == "_deny_retired_saved_cohort_replay"

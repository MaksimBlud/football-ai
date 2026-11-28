"""Outcome-blind tests for the permanently retired saved-cohort replay path."""
import ast
import importlib.util
from pathlib import Path

import pytest


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
FORBIDDEN_IO_CALLS = {
    "open", "read_text", "read_bytes", "write_text", "write_bytes", "mkdir",
    "unlink", "rmdir", "get", "post", "put", "delete", "urlopen", "download",
    "dump", "to_pickle", "run", "system", "connect", "create_client",
}
FORBIDDEN_IMPORTS = {
    "argparse", "requests", "httpx", "urllib", "urllib3", "supabase",
    "numpy", "pandas", "scipy", "sklearn", "joblib", "pickle", "subprocess",
    "socket", "os",
}


def _tree():
    return ast.parse(SCRIPT.read_text(encoding="utf-8"))


def _functions():
    return {
        node.name: node
        for node in _tree().body
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


def _load_retired_module():
    spec = importlib.util.spec_from_file_location("retired_v2_saved_cohort_replay", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    assert _first_call_name(functions["_load_saved_targets_after_gate"]) == "_deny_retired_saved_cohort_replay"


def test_cli_is_retired_before_argument_parsing():
    assert _first_call_name(_functions()["main"]) == "_deny_retired_saved_cohort_replay"


def test_retired_module_has_no_network_or_filesystem_implementation():
    tree = _tree()
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {"__future__"}
    assert not imported.intersection(FORBIDDEN_IMPORTS)

    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    assert not called.intersection(FORBIDDEN_IO_CALLS)


def test_retired_module_has_no_embedded_target_cohort_or_result_mapping():
    tree = _tree()
    assignments = [
        node for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    assigned_names = set()
    for node in assignments:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                assigned_names.add(target.id)
    assert "TARGETS" not in assigned_names
    assert "RESULT_TO_INT" not in assigned_names


def test_runtime_entrypoints_raise_before_touching_supplied_inputs():
    class Untouchable:
        def __getattribute__(self, name):
            raise AssertionError(f"retired replay inspected input before denial: {name}")

    module = _load_retired_module()
    calls = (
        lambda: module.load_module(Untouchable(), Untouchable()),
        lambda: module.load_frozen_modules(Untouchable()),
        lambda: module.download_csv(Untouchable()),
        lambda: module.build_training_frame(Untouchable()),
        lambda: module.build_target_features(Untouchable(), Untouchable()),
        lambda: module.validate_targets(),
        lambda: module.replay(Untouchable()),
        lambda: module.assert_same_frozen_replay(Untouchable()),
        lambda: module.restore_frozen_candidate_from_training_history(Untouchable()),
        lambda: module._require_training_data_access(),
        lambda: module._require_post_outcome_replay_gate(),
        lambda: module._load_saved_targets_after_gate(),
        lambda: module.main(),
    )
    for call in calls:
        with pytest.raises(PermissionError, match="permanently retired"):
            call()

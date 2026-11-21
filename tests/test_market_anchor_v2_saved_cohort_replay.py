"""Outcome-blind static safety checks for the quarantined saved-cohort replay."""
import ast
from pathlib import Path


SCRIPT = Path("market_anchor_v2_saved_cohort_replay.py")


def _tree():
    # Replace the lazy target-literal body before parsing. This test validates
    # gate structure without parsing or materializing protected target rows.
    source = SCRIPT.read_text(encoding="utf-8")
    start = source.index("def _load_saved_targets_after_gate")
    end = source.index("\n\ndef ", start)
    safe_stub = (
        "def _load_saved_targets_after_gate() -> tuple[dict[str, object], ...]:\n"
        "    _require_post_outcome_replay_gate()\n"
        "    return ()\n"
    )
    return ast.parse(source[:start] + safe_stub + source[end:])


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


def _calls_in(node):
    return {
        call.func.id
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }


def test_post_outcome_entrypoints_fail_closed_before_reading_targets():
    functions = _functions()
    for name in (
        "validate_targets",
        "build_target_features",
        "replay",
        "assert_same_frozen_replay",
    ):
        assert _first_call_name(functions[name]) == "_require_post_outcome_replay_gate"


def test_training_entrypoints_require_rights_before_any_source_access():
    functions = _functions()
    for name in (
        "download_csv",
        "build_training_frame",
        "restore_frozen_candidate_from_training_history",
    ):
        assert _first_call_name(functions[name]) == "_require_training_data_access"


def test_training_access_requires_provider_training_and_private_capture_rights():
    calls = _calls_in(_functions()["_require_training_data_access"])
    assert "require_ai_model_training_permission" in calls
    assert "require_v2_source_capture_access" in calls


def test_post_outcome_gate_is_an_unconditional_permission_error():
    gate = _functions()["_require_post_outcome_replay_gate"]
    assert len(gate.body) == 2
    assert isinstance(gate.body[0], ast.Expr)  # docstring
    raised = gate.body[1]
    assert isinstance(raised, ast.Raise)
    assert isinstance(raised.exc, ast.Call)
    assert isinstance(raised.exc.func, ast.Name)
    assert raised.exc.func.id == "PermissionError"


def test_default_cli_path_is_gated_before_replay_call():
    main = _functions()["main"]
    gate_lines = [
        node.lineno for node in ast.walk(main)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_require_post_outcome_replay_gate"
    ]
    replay_lines = [
        node.lineno for node in ast.walk(main)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "replay"
    ]
    assert gate_lines and replay_lines
    assert min(gate_lines) < min(replay_lines)


def test_saved_target_literal_is_lazy_and_not_a_module_level_binding():
    tree = _tree()
    module_assignments = [
        node for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    assert not any(
        isinstance(target, ast.Name) and target.id == "TARGETS"
        for node in module_assignments
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
    )
    assert _first_call_name(_functions()["_load_saved_targets_after_gate"]) == "_require_post_outcome_replay_gate"

def test_target_feature_builder_materializes_targets_only_after_gate():
    node = _functions()["build_target_features"]
    call_lines = {
        call.func.id: call.lineno
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }
    assert call_lines["_require_post_outcome_replay_gate"] < call_lines["_load_saved_targets_after_gate"]
    assert call_lines["_load_saved_targets_after_gate"] < call_lines["require_v2_source_capture_access"]
    assert call_lines["require_v2_source_capture_access"] < call_lines["require_v2_inference_access"]
    assert call_lines["require_v2_inference_access"] < call_lines["download_csv"]



def test_saved_target_loader_contains_no_embedded_target_records():
    import ast
    from pathlib import Path

    source_path = Path(__file__).resolve().parents[1] / "market_anchor_v2_saved_cohort_replay.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    loader = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_load_saved_targets_after_gate"
    )
    assert len(loader.body) == 2
    call = loader.body[0]
    assert isinstance(call, ast.Expr)
    assert isinstance(call.value, ast.Call)
    assert isinstance(call.value.func, ast.Name)
    assert call.value.func.id == "_require_post_outcome_replay_gate"
    assert isinstance(loader.body[1], ast.Raise)
    assert not any(isinstance(node, (ast.Dict, ast.List, ast.Tuple)) for node in ast.walk(loader))

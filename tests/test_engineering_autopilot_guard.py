"""Tests for bounded autonomous coding safety."""
import pytest
from engineering_autopilot_guard import UnsafeAgentChange, parse_status, validate_paths


def files(tmp_path):
    for name in (
        "static/match.html", "product_snapshot_store.py",
        "tests/test_product_ui_contract.py",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("baseline")
    return tmp_path


def test_frontend_allowed(tmp_path):
    root = files(tmp_path)
    assert validate_paths("frontend", [(" M", "static/match.html")], root) == ["static/match.html"]


def test_backend_path_forbidden_to_frontend(tmp_path):
    root = files(tmp_path)
    with pytest.raises(UnsafeAgentChange, match="out-of-scope"):
        validate_paths("frontend", [(" M", "product_snapshot_store.py")], root)


def test_generated_gemini_files_are_never_staged(tmp_path):
    root = files(tmp_path)
    entries = [
        ("??", ".gemini/settings.json"), ("??", "gemini-artifacts/stdout.log"),
        (" M", "static/match.html"),
    ]
    assert validate_paths("frontend", entries, root) == ["static/match.html"]


def test_only_generated_files_is_failure(tmp_path):
    root = files(tmp_path)
    with pytest.raises(UnsafeAgentChange, match="no allowed code changes"):
        validate_paths("frontend", [("??", "gemini-artifacts/stderr.log")], root)


def test_untracked_and_deleted_files_rejected(tmp_path):
    root = files(tmp_path)
    with pytest.raises(UnsafeAgentChange, match="only modifications"):
        validate_paths("frontend", [("??", "static/match.html")], root)
    with pytest.raises(UnsafeAgentChange, match="rename/copy/delete"):
        parse_status(b" D static/match.html\0")


def test_symlink_rejected(tmp_path):
    root = files(tmp_path)
    (root / "static/match.html").unlink()
    (root / "static/match.html").symlink_to("../tests/test_product_ui_contract.py")
    with pytest.raises(UnsafeAgentChange, match="not a regular"):
        validate_paths("frontend", [(" M", "static/match.html")], root)


def test_nul_parser_and_invalid_formats():
    assert parse_status(b" M static/match.html\0?? .gemini/settings.json\0") == [
        (" M", "static/match.html"), ("??", ".gemini/settings.json"),
    ]
    with pytest.raises(UnsafeAgentChange, match="incomplete"):
        parse_status(b" M static/match.html")
    with pytest.raises(UnsafeAgentChange, match="rename/copy/delete"):
        parse_status(b"R  static/match.html\0oldname\0")


def test_role_unknown_and_duplicate_paths(tmp_path):
    root = files(tmp_path)
    with pytest.raises(UnsafeAgentChange, match="unknown role"):
        validate_paths("other", [(" M", "static/match.html")], root)
    with pytest.raises(UnsafeAgentChange, match="duplicate"):
        validate_paths("frontend", [(" M", "static/match.html"), (" M", "static/match.html")], root)

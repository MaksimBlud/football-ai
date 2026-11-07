"""Keep the original MARKET_ANCHOR_1X2_V2 runtime isolated from legacy XGBoost/pickle models.

The V2 residual implementation intentionally reuses the research-only
market_anchor_1x2_v1 helpers. That is not the retired XGBoost production model:
the full local import closure must remain free of xgboost/joblib/pickle model IO.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = (
    "market_anchor_1x2_v2_shadow.py",
    "serie_a_v2_frozen_shadow_preview.py",
    "serie_a_v2_asof_feature_manifest.py",
    "serie_a_v2_forward_capture.py",
    "serie_a_v2_attest_real_source.py",
    "serie_a_v2_current_form_source_capture.py",
    "serie_a_v2_current_form_forward_capture.py",
)
FORBIDDEN_IMPORT_ROOTS = frozenset({"xgboost", "joblib", "pickle"})
FORBIDDEN_CALLS = frozenset({
    "joblib.load",
    "joblib.dump",
    "pickle.load",
    "pickle.dump",
    "pandas.read_pickle",
    "pandas.to_pickle",
    "pd.read_pickle",
    "pd.to_pickle",
})


def _local_module_path(module: str) -> Path | None:
    if not module or module.startswith("."):
        return None
    parts = module.split(".")
    source = ROOT.joinpath(*parts).with_suffix(".py")
    if source.is_file():
        return source
    package = ROOT.joinpath(*parts, "__init__.py")
    return package if package.is_file() else None


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _import_modules(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_original_v2_import_closure_excludes_legacy_xgboost_and_pickle_model_io():
    pending = [ROOT / relative for relative in ENTRYPOINTS]
    visited: set[Path] = set()
    violations: list[str] = []

    while pending:
        path = pending.pop()
        if path in visited:
            continue
        assert path.is_file(), f"missing original V2 runtime source: {path.name}"
        visited.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for module in _import_modules(tree):
            root = module.split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                violations.append(f"{path.name}: forbidden import {module}")
            local_path = _local_module_path(module)
            if local_path is not None and local_path not in visited:
                pending.append(local_path)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            call_name = _dotted_name(node.func)
            if call_name in FORBIDDEN_CALLS:
                violations.append(f"{path.name}: forbidden model IO call {call_name}")
            if call_name in {"Path", "open"}:
                for argument in node.args:
                    if (
                        isinstance(argument, ast.Constant)
                        and isinstance(argument.value, str)
                        and ".pkl" in argument.value.lower()
                    ):
                        violations.append(
                            f"{path.name}: production pickle path passed to {call_name}"
                        )

    assert ROOT / "market_anchor_1x2_v1.py" in visited, (
        "the original V2's documented research residual helper was not audited"
    )
    assert not violations, "\n".join(sorted(violations))

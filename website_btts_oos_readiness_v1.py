"""Independent BTTS source-readiness evaluator for Issue #585."""
from website_goal_source_readiness import evaluate_source_readiness


def evaluate():
    return evaluate_source_readiness("BTTS")

"""Independent O/U 2.5 source-readiness evaluator for Issue #584."""
from website_goal_source_readiness import evaluate_source_readiness


def evaluate():
    return evaluate_source_readiness("OU25")

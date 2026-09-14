from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/exact-main-vercel-deploy.yml"


def test_public_proof_waits_for_bounded_alias_propagation_before_route_smoke():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "for attempt in $(seq 1 12); do" in source
    assert 'if [ "$PUBLIC_SHA" = "$SOURCE_SHA" ]; then' in source
    assert "sleep 5" in source
    assert "did not converge to exact Git source SHA within 60 seconds" in source

    poll_index = source.index("for attempt in $(seq 1 12); do")
    route_index = source.index(
        "for path in /product-market-view /portfolio-risk-view /production-readiness-view; do",
        poll_index,
    )
    assert poll_index < route_index


def test_public_proof_remains_fail_closed_after_timeout():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert 'if [ "$PUBLIC_SHA" != "$SOURCE_SHA" ]; then' in source
    assert 'cat /tmp/prod-health.json 2>/dev/null || true' in source
    assert "exit 1" in source

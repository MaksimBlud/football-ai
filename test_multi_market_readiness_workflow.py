from pathlib import Path


def test_live_readiness_verification_uses_paginated_capability_shape():
    source = Path(
        ".github/workflows/multi-market-activation-status.yml"
    ).read_text(encoding="utf-8")

    assert "stored['sample_limit']" not in source
    assert "stored['page_size']" in source
    assert "stored['pages_inspected']" in source
    assert "stored['rows_inspected']" in source
    assert "stored['scan_complete']" in source
    assert "p['paid_provider_requests']==0" in source
    assert "p['paid_provider_credits']==0" in source
    assert "plan['paid_provider_requests']==0" in source
    assert "plan['paid_provider_credits']==0" in source

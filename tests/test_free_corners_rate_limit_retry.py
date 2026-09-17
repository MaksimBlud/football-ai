from types import SimpleNamespace

import free_corners_rate_limit_retry as retry
import free_corners_signal_screen_v1 as screen


def test_retry_after_seconds_is_honored_with_safety_buffer():
    assert retry._header_wait_seconds({"Retry-After": "10"}, now_epoch=1000.0) == 12.0


def test_reset_epoch_is_honored_with_safety_buffer():
    assert retry._header_wait_seconds({"X-RateLimit-Reset": "1010"}, now_epoch=1000.0) == 12.0


def test_missing_reset_headers_fail_closed():
    assert retry._header_wait_seconds({}, now_epoch=1000.0) is None


def test_429_then_success_counts_both_http_attempts(monkeypatch):
    responses = [
        SimpleNamespace(status_code=429, headers={"Retry-After": "0"}),
        SimpleNamespace(
            status_code=200,
            headers={},
            raise_for_status=lambda: None,
            json=lambda: {"success": 1, "data": []},
        ),
    ]
    calls = []

    def fake_get(*args, **kwargs):
        calls.append((args, kwargs))
        return responses.pop(0)

    sleeps = []
    # The transport timestamps both the pacing check and the completed request
    # for each HTTP attempt. Four values therefore cover a 429 + success pair.
    monotonic_values = iter([0.0, 0.0, 10.0, 10.0])
    monkeypatch.setattr(retry.requests, "get", fake_get)
    monkeypatch.setattr(retry.time, "sleep", lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr(retry.time, "monotonic", lambda: next(monotonic_values))

    client = screen.ProviderClient(key="secret")
    payload = retry._rate_limit_aware_get(client, "/x", params={})

    assert payload == {"success": 1, "data": []}
    assert client.request_count == 2
    assert len(calls) == 2
    assert retry.RESET_SAFETY_SECONDS in sleeps


def test_429_without_reset_header_does_not_retry(monkeypatch):
    response = SimpleNamespace(status_code=429, headers={})
    calls = []
    monkeypatch.setattr(retry.requests, "get", lambda *a, **k: calls.append(1) or response)
    monkeypatch.setattr(retry.time, "monotonic", lambda: 0.0)
    client = screen.ProviderClient(key="secret")
    try:
        retry._rate_limit_aware_get(client, "/x", params={})
    except RuntimeError as exc:
        assert "without a usable" in str(exc)
    else:
        raise AssertionError("expected fail-closed RuntimeError")
    assert client.request_count == 1
    assert len(calls) == 1

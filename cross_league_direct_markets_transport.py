"""Transport-only launcher for CROSS_LEAGUE_DIRECT_MARKETS_V1.

The research contract and evaluator live in cross_league_direct_markets_v1.py.
This launcher changes only HTTP transport: it retries the same official
football-data.co.uk CSV path on the canonical host when the www endpoint is
redirected to an unusable loopback address by the CI/network edge.
"""
from __future__ import annotations

from urllib.parse import urlparse

import requests

import cross_league_direct_markets_v1 as experiment

_ORIGINAL_GET = requests.get
_OFFICIAL_HOSTS = {"www.football-data.co.uk", "football-data.co.uk"}
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/150.0 Safari/537.36 football-ai-research/1.0"
)


def _candidate_urls(url: str) -> tuple[str, ...]:
    parsed = urlparse(url)
    if parsed.hostname not in _OFFICIAL_HOSTS:
        raise RuntimeError(f"unexpected historical source host: {parsed.hostname!r}")
    canonical = url.replace("https://www.football-data.co.uk/", "https://football-data.co.uk/", 1)
    return (url,) if canonical == url else (url, canonical)


def _official_get(url: str, *args, **kwargs):
    timeout = kwargs.pop("timeout", 60)
    caller_headers = dict(kwargs.pop("headers", {}) or {})
    headers = {"User-Agent": _USER_AGENT, "Accept": "text/csv,*/*;q=0.8", **caller_headers}
    errors: list[str] = []
    for candidate in _candidate_urls(url):
        try:
            response = _ORIGINAL_GET(
                candidate,
                *args,
                timeout=timeout,
                headers=headers,
                allow_redirects=True,
                **kwargs,
            )
            final_host = urlparse(response.url).hostname
            if final_host in {"127.0.0.1", "localhost", "::1"}:
                raise RuntimeError(f"official endpoint redirected to loopback: {response.url}")
            response.raise_for_status()
            if not response.content:
                raise RuntimeError("official endpoint returned an empty body")
            return response
        except (requests.RequestException, RuntimeError) as exc:
            errors.append(f"{candidate}: {type(exc).__name__}: {exc}")
    raise RuntimeError("all official Football-Data transports failed: " + " | ".join(errors))


def main() -> None:
    experiment.requests.get = _official_get
    experiment.main()


if __name__ == "__main__":
    main()

"""Pinned transport for independent D1/F1 lead-lag replication.

Uses official Football-Data first. If the official host is unavailable or
redirects to loopback in CI, falls back to exact files at a frozen public
GitHub commit and verifies every body against its preregistered Git blob SHA.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

import cross_market_lead_lag_independent_replication_v1 as experiment


_ORIGINAL_GET = requests.get
_OFFICIAL_HOSTS = {"www.football-data.co.uk", "football-data.co.uk"}
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/150.0 Safari/537.36 football-ai-research/1.0"
)
_MIRROR_REPO = "Emire221/kahin"
_MIRROR_COMMIT = "97c22f31564baafbd18ef818bb2df9fcb49319bc"

_SEASON_NAMES = {
    "1920": "2019-2020",
    "2021": "2020-2021",
    "2122": "2021-2022",
    "2223": "2022-2023",
    "2324": "2023-2024",
    "2425": "2024-2025",
    "2526": "2025-2026",
}

_BLOB_SHAS = {
    ("D1", "1920"): "a07e4ab36464bd1c4b62c2e98e4559aff4fdb4ef",
    ("D1", "2021"): "0d3370c801e43c5dcb9012e405678dc5179b325d",
    ("D1", "2122"): "5796451d8caa093b8176f6eecf82051a239604f6",
    ("D1", "2223"): "406b28aee2ccd37177eec474447f4a3325247db4",
    ("D1", "2324"): "54efdb13aa7b537a80aca0a2378942d373594c06",
    ("D1", "2425"): "5ab934bebe32bfd689d97eb8303795dac4e8c407",
    ("D1", "2526"): "e8b2bffe7a16a794feb6985fe5ea50dcdd2f4137",
    ("F1", "1920"): "4e2cd6384a05d10cd9ad1a4c1b4d087d60fddd45",
    ("F1", "2021"): "0227119200af3698163fb0265d0910e377bcf335",
    ("F1", "2122"): "b98b8533c186704863ef63f25f65be770a4289d6",
    ("F1", "2223"): "f6cbe993e0a6be9322026acaed8015cb5e5ee14b",
    ("F1", "2324"): "3836a0b1a91ca4e9f97a61bbe3717b5fddd1a131",
    ("F1", "2425"): "fe5478bb28dd899b9646207ffc8e01bbb2dfc5ff",
    ("F1", "2526"): "cb484bdf3522fa081be58eefb497065fb4912810",
}

_REQUEST_RE = re.compile(
    r"/mmz4281/(?P<code>1920|2021|2122|2223|2324|2425|2526)/"
    r"(?P<comp>D1|F1)\.csv$"
)


@dataclass(frozen=True)
class MirrorSpec:
    path: str
    blob_sha: str


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _mirror_spec(url: str) -> MirrorSpec:
    parsed = urlparse(url)
    match = _REQUEST_RE.search(parsed.path)
    if parsed.hostname not in _OFFICIAL_HOSTS or match is None:
        raise RuntimeError(f"unexpected historical source URL: {url!r}")

    code = match.group("code")
    comp = match.group("comp")
    expected = _BLOB_SHAS.get((comp, code))
    if expected is None:
        raise RuntimeError(f"unregistered mirror identity: {comp}/{code}")

    season = _SEASON_NAMES[code]
    return MirrorSpec(
        path=f"data/raw_csv/{comp}_{season}.csv",
        blob_sha=expected,
    )


def _candidate_urls(url: str) -> tuple[str, ...]:
    parsed = urlparse(url)
    if parsed.hostname not in _OFFICIAL_HOSTS:
        raise RuntimeError(
            f"unexpected historical source host: {parsed.hostname!r}"
        )
    canonical = url.replace(
        "https://www.football-data.co.uk/",
        "https://football-data.co.uk/",
        1,
    )
    return (url,) if canonical == url else (url, canonical)


def _download(url: str, *, timeout: int, headers: dict, **kwargs):
    response = _ORIGINAL_GET(
        url,
        timeout=timeout,
        headers=headers,
        allow_redirects=True,
        **kwargs,
    )
    final_host = urlparse(response.url).hostname
    if final_host in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError(
            f"endpoint redirected to loopback: {response.url}"
        )
    response.raise_for_status()
    if not response.content:
        raise RuntimeError("endpoint returned an empty body")
    return response


def _official_or_pinned_mirror_get(url: str, *args, **kwargs):
    timeout = kwargs.pop("timeout", 60)
    caller_headers = dict(kwargs.pop("headers", {}) or {})
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "text/csv,*/*;q=0.8",
        **caller_headers,
    }
    errors: list[str] = []

    for candidate in _candidate_urls(url):
        try:
            return _download(
                candidate,
                timeout=timeout,
                headers=headers,
                *args,
                **kwargs,
            )
        except (requests.RequestException, RuntimeError) as exc:
            errors.append(
                f"{candidate}: {type(exc).__name__}: {exc}"
            )

    spec = _mirror_spec(url)
    mirror_url = (
        f"https://raw.githubusercontent.com/{_MIRROR_REPO}/"
        f"{_MIRROR_COMMIT}/{spec.path}"
    )
    try:
        response = _download(
            mirror_url,
            timeout=timeout,
            headers=headers,
            *args,
            **kwargs,
        )
        actual = _git_blob_sha(response.content)
        if actual != spec.blob_sha:
            raise RuntimeError(
                f"pinned mirror blob mismatch for {spec.path}: "
                f"{actual} != {spec.blob_sha}"
            )
        print(
            "FOOTBALL_DATA_REPLICATION_TRANSPORT_FALLBACK "
            f"path={spec.path} repo={_MIRROR_REPO} "
            f"commit={_MIRROR_COMMIT} blob={actual}"
        )
        return response
    except (requests.RequestException, RuntimeError) as exc:
        errors.append(
            f"{mirror_url}: {type(exc).__name__}: {exc}"
        )

    raise RuntimeError(
        "all Football-Data transports failed: " + " | ".join(errors)
    )


def main() -> None:
    experiment.requests.get = _official_or_pinned_mirror_get
    experiment.main()


if __name__ == "__main__":
    main()

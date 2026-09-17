"""Transport-only launcher for CROSS_LEAGUE_DIRECT_MARKETS_V1.

The research contract and evaluator live in cross_league_direct_markets_v1.py.
This module does not change targets, features, splits, estimators, or gates.

GitHub Actions currently redirects both official football-data.co.uk hosts to a
loopback address.  When that transport failure occurs, this launcher may read
pinned *raw copies of the same Football-Data season CSVs* from public GitHub
mirrors.  Every accepted mirror body is verified against its pinned Git blob
SHA before it is returned to the unchanged evaluator.

Mirror provenance was checked before this fallback was added:
- Emire221/kahin documents data/raw_csv as raw football-data.co.uk files;
- yusufislamoruk/football-prediction-bot contains later complete season files;
- overlapping SP1/I1 seasons and EPL 2022-23..2024-25 have identical Git blob
  SHAs across the mirrors, supporting byte-level source continuity.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

import cross_league_direct_markets_v1 as experiment

_ORIGINAL_GET = requests.get
_OFFICIAL_HOSTS = {"www.football-data.co.uk", "football-data.co.uk"}
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/150.0 Safari/537.36 football-ai-research/1.0"
)
_OLD_REPO = "Emire221/kahin"
_OLD_COMMIT = "97c22f31564baafbd18ef818bb2df9fcb49319bc"
_NEW_REPO = "yusufislamoruk/football-prediction-bot"
_NEW_COMMIT = "47ca08e08f46d16a8f6a0494777b1e16ae5562b3"


@dataclass(frozen=True)
class MirrorSpec:
    repo: str
    commit: str
    path: str
    blob_sha: str


_OLD_NAMES = {
    "1617": "2016-2017",
    "1718": "2017-2018",
    "1819": "2018-2019",
    "1920": "2019-2020",
    "2021": "2020-2021",
    "2122": "2021-2022",
}
_NEW_NAMES = {
    "2223": "2022-23",
    "2324": "2023-24",
    "2425": "2024-25",
    "2526": "2025-26",
}
_NEW_FOLDERS = {
    "E0": "premier_league",
    "SP1": "la_liga",
    "I1": "serie_a",
}

# Pinned Git blob SHAs for the exact CSV bodies used by the frozen experiment.
_BLOB_SHAS = {
    ("E0", "1617"): "5c3b3164701a00476b3c823b243dcba58364d52a",
    ("E0", "1718"): "5215909cc4eec26b143d8ec9f6187724e91e6956",
    ("E0", "1819"): "c751806645cadb8dad71af29ada240fed3a41d23",
    ("E0", "1920"): "7fbf67f417c734ee8aec7e9f02279de9664f1aec",
    ("E0", "2021"): "a1b6b753633a9a6aeea400478ebb46e3a7357651",
    ("E0", "2122"): "91f1f768e1f6288b5a3f9b414847bdbbf6746c36",
    ("E0", "2223"): "d938f7b58fd92aafefa63effe3548afb27b17188",
    ("E0", "2324"): "5bc9399ba12ef3ca732477dc207b52ca09edd00e",
    ("E0", "2425"): "7ee880ccda92e44e6512d5cd3033ab3af1eb1bd2",
    ("E0", "2526"): "04aaaca6e52d5bff73cdd620a15647c76c936157",
    ("SP1", "1617"): "0e930aff2055ffeb0835e5cb883af38742b4b149",
    ("SP1", "1718"): "0211b3df66046f02c1d92552d26d44996f04fa5a",
    ("SP1", "1819"): "cba8744b19166b571105479091cbf435d2a5970e",
    ("SP1", "1920"): "2a9e64d0ed010355cd76d2f5d3e6060dd0caeb0d",
    ("SP1", "2021"): "5d204a764e4ffc11e35dc5bf4f4085beaad3ee6d",
    ("SP1", "2122"): "0e027aa2bdfb0b2245f0bcb60d9a02573aa6e6ce",
    ("SP1", "2223"): "6b1d8a09f2405823304a37005498d28e4bf2757d",
    ("SP1", "2324"): "5d16cac7c7f3b56522db60b9e32972a66c17544a",
    ("SP1", "2425"): "0111b0a2c81634ec6c6dcd6d0d9d26752af14519",
    ("SP1", "2526"): "f780d713ef62a2130ef56296a5a2c8b5a64ef9f4",
    ("I1", "1617"): "52effb638f69eae535ea61c726c618f9d9094c90",
    ("I1", "1718"): "fbda3ef9b947c883cc41da147d29094fac5f5592",
    ("I1", "1819"): "d6689243cf6dff2f795ff904d7dab8db7909b5b5",
    ("I1", "1920"): "74625ab282b34a245a7bcf02639827b508e0b68c",
    ("I1", "2021"): "1fb2ecfe45435e8c325d0d53c10846ffecb6ca39",
    ("I1", "2122"): "934f80893122fc6814573ee38aecf4bc501c491b",
    ("I1", "2223"): "007791fa10d9f3854a8a7fa43521112e66f32fd2",
    ("I1", "2324"): "2d8202f554d54fa289874ef69ef198e91b2de70a",
    ("I1", "2425"): "c4210a32bbdcea6f84d07ac790ff789e00561d60",
    ("I1", "2526"): "7385c811da8c8fa65aaad091653c8849458b23e5",
}

_REQUEST_RE = re.compile(r"/mmz4281/(?P<code>\d{4})/(?P<comp>E0|SP1|I1)\.csv$")


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
    if code in _OLD_NAMES:
        season = _OLD_NAMES[code]
        return MirrorSpec(
            repo=_OLD_REPO,
            commit=_OLD_COMMIT,
            path=f"data/raw_csv/{comp}_{season}.csv",
            blob_sha=expected,
        )
    season = _NEW_NAMES[code]
    return MirrorSpec(
        repo=_NEW_REPO,
        commit=_NEW_COMMIT,
        path=f"data/raw/{_NEW_FOLDERS[comp]}/{comp}_{season}.csv",
        blob_sha=expected,
    )


def _candidate_urls(url: str) -> tuple[str, ...]:
    parsed = urlparse(url)
    if parsed.hostname not in _OFFICIAL_HOSTS:
        raise RuntimeError(f"unexpected historical source host: {parsed.hostname!r}")
    canonical = url.replace("https://www.football-data.co.uk/", "https://football-data.co.uk/", 1)
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
        raise RuntimeError(f"endpoint redirected to loopback: {response.url}")
    response.raise_for_status()
    if not response.content:
        raise RuntimeError("endpoint returned an empty body")
    return response


def _official_or_pinned_mirror_get(url: str, *args, **kwargs):
    timeout = kwargs.pop("timeout", 60)
    caller_headers = dict(kwargs.pop("headers", {}) or {})
    headers = {"User-Agent": _USER_AGENT, "Accept": "text/csv,*/*;q=0.8", **caller_headers}
    errors: list[str] = []

    for candidate in _candidate_urls(url):
        try:
            return _download(candidate, timeout=timeout, headers=headers, *args, **kwargs)
        except (requests.RequestException, RuntimeError) as exc:
            errors.append(f"{candidate}: {type(exc).__name__}: {exc}")

    spec = _mirror_spec(url)
    mirror_url = (
        f"https://raw.githubusercontent.com/{spec.repo}/{spec.commit}/{spec.path}"
    )
    try:
        response = _download(mirror_url, timeout=timeout, headers=headers, *args, **kwargs)
        actual = _git_blob_sha(response.content)
        if actual != spec.blob_sha:
            raise RuntimeError(
                f"pinned mirror blob mismatch for {spec.path}: {actual} != {spec.blob_sha}"
            )
        print(
            "FOOTBALL_DATA_TRANSPORT_FALLBACK "
            f"path={spec.path} repo={spec.repo} commit={spec.commit} blob={actual}"
        )
        return response
    except (requests.RequestException, RuntimeError) as exc:
        errors.append(f"{mirror_url}: {type(exc).__name__}: {exc}")

    raise RuntimeError("all Football-Data transports failed: " + " | ".join(errors))


def main() -> None:
    experiment.requests.get = _official_or_pinned_mirror_get
    experiment.main()


if __name__ == "__main__":
    main()

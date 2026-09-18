"""Transport-only retry wrapper for FREE_CORNERS_SIGNAL_SCREEN_V1.

This module does not change the frozen sample, model, features, metrics or verdict.
It only makes 5DollarFootballAPI HTTP 429 handling honor provider reset headers while
counting every actual HTTP attempt against the existing hard request budget.
"""
from __future__ import annotations

import email.utils
import time
from datetime import datetime, timezone
from typing import Any

import requests

import free_corners_signal_screen_v1 as screen

MAX_RATE_LIMIT_RETRIES = 2
RESET_SAFETY_SECONDS = 2.0
MAX_RESET_WAIT_SECONDS = 3700.0


def _header_wait_seconds(headers: Any, *, now_epoch: float | None = None) -> float | None:
    now_epoch = time.time() if now_epoch is None else now_epoch
    retry_after = str(headers.get("Retry-After") or "").strip()
    if retry_after:
        try:
            value = float(retry_after)
            if value >= 0:
                return min(value + RESET_SAFETY_SECONDS, MAX_RESET_WAIT_SECONDS)
        except ValueError:
            try:
                parsed = email.utils.parsedate_to_datetime(retry_after)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return min(max(0.0, parsed.timestamp() - now_epoch) + RESET_SAFETY_SECONDS, MAX_RESET_WAIT_SECONDS)
            except Exception:
                pass

    reset = str(headers.get("X-RateLimit-Reset") or headers.get("X-Ratelimit-Reset") or "").strip()
    if reset:
        try:
            reset_epoch = float(reset)
            return min(max(0.0, reset_epoch - now_epoch) + RESET_SAFETY_SECONDS, MAX_RESET_WAIT_SECONDS)
        except ValueError:
            pass
    return None


def _rate_limit_aware_get(self: screen.ProviderClient, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
    retries = 0
    while True:
        if self.request_count >= screen.MAX_PROVIDER_REQUESTS:
            raise RuntimeError("provider request budget exceeded")

        now = time.monotonic()
        if self.last_request_at is not None:
            remaining = screen.REQUEST_INTERVAL_SECONDS - (now - self.last_request_at)
            if remaining > 0:
                time.sleep(remaining)

        response = requests.get(
            screen.BASE_URL + path,
            headers={"Authorization": f"Bearer {self.key}", "Accept": "application/json"},
            params=params,
            timeout=45,
        )
        self.last_request_at = time.monotonic()
        self.request_count += 1

        if response.status_code == 429:
            if retries >= MAX_RATE_LIMIT_RETRIES:
                raise RuntimeError("provider rate limit remained active after bounded retries")
            wait_seconds = _header_wait_seconds(response.headers)
            if wait_seconds is None:
                raise RuntimeError("provider returned HTTP 429 without a usable Retry-After/X-RateLimit-Reset header")
            retries += 1
            print(
                f"Provider rate limit reached; waiting {wait_seconds:.1f}s before bounded retry "
                f"{retries}/{MAX_RATE_LIMIT_RETRIES}. Request attempts used={self.request_count}/{screen.MAX_PROVIDER_REQUESTS}",
                flush=True,
            )
            time.sleep(wait_seconds)
            continue

        response.raise_for_status()
        payload = response.json()
        if payload.get("success") != 1:
            raise RuntimeError(f"provider API failure: {payload.get('error')}")
        return payload


def install_rate_limit_retry() -> None:
    screen.ProviderClient.get = _rate_limit_aware_get


def main() -> None:
    install_rate_limit_retry()
    screen.main()


if __name__ == "__main__":
    main()

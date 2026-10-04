"""Compact Gemini REST client for Research Orchestrator V4."""
from __future__ import annotations

import json
import re
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

import requests

DEFAULT_MODEL = "gemini-3.5-flash-lite"


class RetryableGeminiError(RuntimeError):
    def __init__(self, message: str, retry_at_utc: str):
        super().__init__(message)
        self.retry_at_utc = retry_at_utc


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_iso(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat().replace("+00:00", "Z")


def parse_json_text(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.I)
        value = re.sub(r"\s*```$", "", value)
    try:
        obj = json.loads(value)
    except json.JSONDecodeError:
        start, end = value.find("{"), value.rfind("}")
        if start < 0 or end <= start:
            raise
        obj = json.loads(value[start:end + 1])
    if not isinstance(obj, dict):
        raise ValueError("Gemini response JSON must be an object")
    return obj


def _response_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Gemini response has no candidates: {payload}")
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text = "".join(str(part.get("text") or "") for part in parts)
    if not text.strip():
        raise RuntimeError(f"Gemini response contains no text: {payload}")
    return text.strip()


def retry_seconds(message: str, header: str | None = None) -> float:
    if header:
        try:
            return max(1.0, float(header))
        except ValueError:
            pass
    match = re.search(r"retry in\s+([0-9.]+)s", message, flags=re.I)
    if match:
        return max(1.0, float(match.group(1)))
    match = re.search(r"retry in\s+(\d+)h(?:(\d+)m)?", message, flags=re.I)
    if match:
        return int(match.group(1)) * 3600 + int(match.group(2) or 0) * 60
    return 3600.0


def gemini_json(
    *,
    api_key: str,
    system_instruction: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_output_tokens: int = 8192,
    post: Callable[..., Any] = requests.post,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Call Gemini once with bounded retries and request JSON output."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.15,
            "maxOutputTokens": max_output_tokens,
            "responseMimeType": "application/json",
        },
    }
    for attempt in range(3):
        response = post(
            url,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=body,
            timeout=180,
        )
        if response.status_code == 200:
            return parse_json_text(_response_text(response.json()))

        message = response.text[:8000]
        if response.status_code not in {429, 500, 502, 503, 504}:
            raise RuntimeError(f"Gemini HTTP {response.status_code}: {message}")

        delay = retry_seconds(message, response.headers.get("Retry-After"))
        if attempt < 2 and delay <= 75:
            sleep(delay + 1)
            continue

        retry_at = utc_now() + timedelta(seconds=max(delay, 3600))
        raise RetryableGeminiError(
            f"Gemini retryable HTTP {response.status_code}: {message}",
            utc_iso(retry_at),
        )
    raise AssertionError("unreachable")

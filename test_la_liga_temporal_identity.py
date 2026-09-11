from __future__ import annotations

import unittest

from la_liga_temporal_identity import (
    TemporalObservationConflictError,
    canonical_observation_key_map,
)


MARKET = {
    "market_home_probability": 0.3716200019171321,
    "market_draw_probability": 0.254562273189,
    "market_away_probability": 0.3738177248938679,
    "market_argmax": "A",
}


def row(
    observation_key: str,
    persisted_at_utc: str,
    *,
    structural_score: float,
    market: dict | None = None,
) -> dict:
    payload = {
        **(market or MARKET),
        "structural_score": structural_score,
        "correction_enabled": structural_score > 0.5,
    }
    return {
        "observation_key": observation_key,
        "event_id": "98222f8385c445cb0cbfae0ab9073abd",
        "snapshot_time_utc": "2026-09-04T16:29:24.526493+00:00",
        "persisted_at_utc": persisted_at_utc,
        "league": "LA_LIGA",
        "payload": payload,
    }


class LaLigaTemporalIdentityTests(unittest.TestCase):
    def test_first_durable_observation_wins_when_only_structure_drifted(self):
        mapping, metrics = canonical_observation_key_map(
            [
                row(
                    "LA_LIGA:new-reconstruction",
                    "2026-09-11T15:45:20+00:00",
                    structural_score=0.826,
                ),
                row(
                    "LA_LIGA:first-prospective",
                    "2026-09-04T16:30:00+00:00",
                    structural_score=0.326,
                ),
            ]
        )

        identity = (
            "98222f8385c445cb0cbfae0ab9073abd",
            "2026-09-04T16:29:24.526493+00:00",
        )
        self.assertEqual(mapping[identity], "LA_LIGA:first-prospective")
        self.assertEqual(metrics.input, 2)
        self.assertEqual(metrics.canonical, 1)
        self.assertEqual(metrics.duplicate_temporal_rows, 1)
        self.assertEqual(metrics.structural_drift_rows, 1)

    def test_duplicate_temporal_identity_with_market_drift_fails_closed(self):
        changed_market = {
            **MARKET,
            "market_home_probability": 0.40,
        }
        with self.assertRaises(TemporalObservationConflictError):
            canonical_observation_key_map(
                [
                    row(
                        "LA_LIGA:first",
                        "2026-09-04T16:30:00+00:00",
                        structural_score=0.326,
                    ),
                    row(
                        "LA_LIGA:later",
                        "2026-09-11T15:45:20+00:00",
                        structural_score=0.826,
                        market=changed_market,
                    ),
                ]
            )

    def test_invalid_persisted_timestamp_fails_closed(self):
        with self.assertRaises(TemporalObservationConflictError):
            canonical_observation_key_map(
                [
                    row(
                        "LA_LIGA:first",
                        "not-a-time",
                        structural_score=0.326,
                    )
                ]
            )

    def test_foreign_league_fails_closed(self):
        candidate = row(
            "LA_LIGA:first",
            "2026-09-04T16:30:00+00:00",
            structural_score=0.326,
        )
        candidate["league"] = "EPL"
        with self.assertRaises(TemporalObservationConflictError):
            canonical_observation_key_map([candidate])


if __name__ == "__main__":
    unittest.main()

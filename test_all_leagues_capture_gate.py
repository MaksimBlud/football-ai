import unittest

from all_leagues_capture_gate import (
    LEAGUES,
    MANIFEST_SCHEMA_VERSION,
    GateInputError,
    evaluate_all_leagues,
)


def manifest_for(entries):
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "leagues": entries,
    }


def complete_entries():
    return [
        {
            "league": league,
            "expected_event_ids": [f"{league}-1", f"{league}-2"],
            "captured_event_ids": [f"{league}-2", f"{league}-1"],
        }
        for league in LEAGUES
    ]


class AllLeaguesCaptureGateTests(unittest.TestCase):
    def test_complete_all_eight_manifest_passes(self):
        result = evaluate_all_leagues(manifest_for(complete_entries()))

        self.assertTrue(result["complete"])
        self.assertEqual(result["league_count"], 8)
        self.assertEqual(
            result["totals"],
            {"EXPECTED": 16, "CAPTURED": 16, "MISSING": 0, "UNEXPECTED": 0},
        )
        self.assertEqual([item["league"] for item in result["leagues"]], list(LEAGUES))

    def test_missing_fixture_is_reported_and_fails_global_gate(self):
        entries = complete_entries()
        entries[1]["captured_event_ids"] = ["serie_a-1"]

        result = evaluate_all_leagues(manifest_for(entries))
        serie_a = result["leagues"][1]

        self.assertFalse(result["complete"])
        self.assertEqual(serie_a["MISSING"], ["serie_a-2"])
        self.assertEqual(serie_a["counts"]["CAPTURED"], 1)
        self.assertEqual(result["totals"]["MISSING"], 1)

    def test_unexpected_capture_is_reported_and_fails_closed(self):
        entries = complete_entries()
        entries[2]["captured_event_ids"].append("la_liga-extra")

        result = evaluate_all_leagues(manifest_for(entries))
        la_liga = result["leagues"][2]

        self.assertFalse(result["complete"])
        self.assertEqual(la_liga["UNEXPECTED"], ["la_liga-extra"])
        self.assertEqual(la_liga["counts"]["CAPTURED"], 2)
        self.assertEqual(result["totals"]["UNEXPECTED"], 1)

    def test_duplicate_expected_event_id_is_rejected(self):
        entries = complete_entries()
        entries[0]["expected_event_ids"] = ["epl-1", "epl-1"]

        with self.assertRaisesRegex(GateInputError, "duplicate epl.expected_event_ids"):
            evaluate_all_leagues(manifest_for(entries))

    def test_duplicate_captured_rows_cannot_inflate_coverage(self):
        entries = complete_entries()
        entries[0]["captured_event_ids"] = ["epl-1", "epl-1", "epl-2"]

        with self.assertRaisesRegex(GateInputError, "duplicate epl.captured_event_ids"):
            evaluate_all_leagues(manifest_for(entries))

    def test_blank_or_non_string_event_ids_are_rejected(self):
        for invalid in (" ", None, 123):
            with self.subTest(invalid=invalid):
                entries = complete_entries()
                entries[0]["expected_event_ids"] = [invalid]
                with self.assertRaises(GateInputError):
                    evaluate_all_leagues(manifest_for(entries))

    def test_missing_collection_ready_league_is_rejected(self):
        entries = complete_entries()[:-1]

        with self.assertRaisesRegex(GateInputError, "primeira_liga"):
            evaluate_all_leagues(manifest_for(entries))

    def test_duplicate_league_entry_is_rejected(self):
        entries = complete_entries()
        entries.append(dict(entries[0]))

        with self.assertRaisesRegex(GateInputError, "duplicate league entry"):
            evaluate_all_leagues(manifest_for(entries))

    def test_output_is_deterministic_for_event_id_order(self):
        entries_a = complete_entries()
        entries_b = complete_entries()
        for entry in entries_b:
            entry["expected_event_ids"].reverse()
            entry["captured_event_ids"].reverse()

        self.assertEqual(
            evaluate_all_leagues(manifest_for(entries_a)),
            evaluate_all_leagues(manifest_for(entries_b)),
        )

    def test_wrong_schema_version_is_rejected(self):
        manifest = manifest_for(complete_entries())
        manifest["schema_version"] = "future_or_stale_schema"

        with self.assertRaisesRegex(GateInputError, "schema_version"):
            evaluate_all_leagues(manifest)


if __name__ == "__main__":
    unittest.main()

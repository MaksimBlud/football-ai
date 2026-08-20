import json
import tempfile
import unittest
from pathlib import Path

from artifact_lifecycle import (
    ARTIFACT_SPECS,
    promote_candidate,
    save_candidate,
    sha256_file,
    validate_candidate,
    verify_production,
)


class ArtifactLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.input_path = self.root / "training.csv"
        self.input_path.write_text("feature,target\n1,0\n")
        self.destination = "football_model_no_odds.pkl"
        self.production = self.root / self.destination
        self.production.write_bytes(b"existing production")
        self.production_hash = sha256_file(self.production)

    def tearDown(self):
        self.temporary.cleanup()

    def create_candidate(self):
        spec = ARTIFACT_SPECS[self.destination]
        return save_candidate(
            {"candidate": True}, self.destination, "test producer",
            [self.input_path], spec["type"], spec["features"], {"seed": 42},
            self.root / "candidates",
        )

    def test_default_candidate_save_does_not_change_production(self):
        candidate, manifest = self.create_candidate()
        self.assertTrue(candidate.is_file())
        self.assertTrue(manifest.is_file())
        self.assertEqual(sha256_file(self.production), self.production_hash)

    def test_verification_reports_missing_required_artifact(self):
        self.assertIn("1x2_calibrator.pkl", verify_production(self.root))

    def test_promotion_dry_run_writes_nothing(self):
        candidate, manifest = self.create_candidate()
        before = {path.relative_to(self.root) for path in self.root.rglob("*")}
        promote_candidate(candidate, manifest, self.destination, self.root, dry_run=True)
        after = {path.relative_to(self.root) for path in self.root.rglob("*")}
        self.assertEqual(before, after)
        self.assertEqual(sha256_file(self.production), self.production_hash)
        self.assertFalse((self.root / "artifacts/production_backups").exists())

    def test_invalid_hash_schema_and_type_are_rejected(self):
        for field, value in (
            ("sha256", "0" * 64),
            ("feature_schema", {"names": ["wrong"], "count": 1}),
            ("artifact_type", "wrong_type"),
        ):
            with self.subTest(field=field):
                candidate, manifest_path = self.create_candidate()
                manifest = json.loads(manifest_path.read_text())
                manifest[field] = value
                manifest_path.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    validate_candidate(candidate, manifest_path, self.destination)


if __name__ == "__main__":
    unittest.main()

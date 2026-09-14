"""Materialize a registered Total Goals bundle into an empty local directory.

This command only downloads and verifies registered bytes.  It does not promote
artifacts into production paths and does not run model inference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from total_goals_artifact_registry import (
    create_privileged_supabase_client,
    materialize_registered_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_sha256", help="Registered goal-artifact-bundle.v1 SHA-256")
    parser.add_argument(
        "--destination",
        type=Path,
        required=True,
        help="Empty directory that will receive verified bundle files",
    )
    args = parser.parse_args()

    client = create_privileged_supabase_client()
    result = materialize_registered_bundle(client, args.bundle_sha256, args.destination)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

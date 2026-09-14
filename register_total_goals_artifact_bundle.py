"""Plan or explicitly register the existing Total Goals production bundle.

Dry-run is the default.  ``--execute`` is required for any Supabase network write.
This command never trains, promotes, or runs model inference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from total_goals_artifact_registry import (
    build_registry_manifest,
    create_privileged_supabase_client,
    register_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Directory containing all four existing Total Goals production artifacts",
    )
    parser.add_argument(
        "--source-note",
        default=None,
        help="Optional human-readable provenance note stored with the immutable registry row",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform private Storage upload + append-only metadata registration",
    )
    args = parser.parse_args()

    if not args.execute:
        manifest = build_registry_manifest(args.root, source_note=args.source_note)
        print(json.dumps({"status": "DRY_RUN", "manifest": manifest}, indent=2, sort_keys=True))
        return 0

    client = create_privileged_supabase_client()
    result = register_bundle(client, args.root, source_note=args.source_note)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

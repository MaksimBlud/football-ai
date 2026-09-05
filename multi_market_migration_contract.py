"""Static safety contract for the three Multi-Market V2 Supabase migrations.

This module does not connect to Supabase or apply DDL. It verifies the exact
research-only migration set before any future authorized admin deployment.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MIGRATION_DIR = Path("supabase/migrations")
EXPECTED = (
    "202609050001_league_multi_market_snapshots.sql",
    "202609050002_league_multi_market_settlements.sql",
    "202609050003_league_corner_results.sql",
)
SNAPSHOT_TABLE = "public.league_multi_market_snapshots"
SETTLEMENT_TABLE = "public.league_multi_market_settlements"
CORNER_TABLE = "public.league_corner_results"

# These operations are outside the preregistered additive-only deployment scope.
FORBIDDEN_PATTERNS = {
    "DROP": r"\bdrop\b",
    "TRUNCATE": r"\btruncate\b",
    "DELETE": r"\bdelete\s+from\b",
    "UPDATE": r"\bupdate\s+\w",
    "ALTER_DROP": r"\balter\s+table\b[\s\S]*?\bdrop\b",
    "ALTER_COLUMN": r"\balter\s+table\b[\s\S]*?\balter\s+column\b",
}


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def audit_migrations(root: Path = MIGRATION_DIR) -> dict:
    files = []
    blockers: list[str] = []
    texts: dict[str, str] = {}

    for name in EXPECTED:
        path = root / name
        if not path.is_file():
            blockers.append(f"MISSING:{name}")
            continue
        text = path.read_text(encoding="utf-8")
        texts[name] = text
        executable = _strip_comments(text).lower()
        forbidden = [label for label, pattern in FORBIDDEN_PATTERNS.items() if re.search(pattern, executable, flags=re.I)]
        if forbidden:
            blockers.append(f"DESTRUCTIVE_SQL:{name}:{','.join(forbidden)}")
        files.append({"name": name, "forbidden_operations": forbidden})

    first = texts.get(EXPECTED[0], "").lower()
    second = texts.get(EXPECTED[1], "").lower()
    third = texts.get(EXPECTED[2], "").lower()

    if first and f"create table if not exists {SNAPSHOT_TABLE}" not in first:
        blockers.append("SNAPSHOT_CREATE_CONTRACT_MISSING")
    if second:
        if f"create table if not exists {SETTLEMENT_TABLE}" not in second:
            blockers.append("SETTLEMENT_CREATE_CONTRACT_MISSING")
        if f"references {SNAPSHOT_TABLE}(snapshot_key)" not in second:
            blockers.append("SETTLEMENT_SNAPSHOT_FK_MISSING")
    if third and f"create table if not exists {CORNER_TABLE}" not in third:
        blockers.append("CORNER_CREATE_CONTRACT_MISSING")

    return {
        "schema_version": "MULTI_MARKET_MIGRATION_CONTRACT_V1",
        "research_only": True,
        "applies_migrations": False,
        "expected_order": list(EXPECTED),
        "files": files,
        "static_contract_ready": not blockers,
        "deployment_path_status": "EXTERNAL_ADMIN_PATH_REQUIRED",
        "blockers": blockers,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_migrations()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if not result["static_contract_ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

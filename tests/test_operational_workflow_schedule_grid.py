import re
from pathlib import Path


WORKFLOW_DIR = Path(__file__).parents[1] / ".github" / "workflows"

SCHEDULED_OPERATIONAL_WORKFLOWS = (
    "epl-live-cycle.yml",
    "epl-results.yml",
    "rpl-live-cycle.yml",
    "serie-a-live-cycle.yml",
    "serie-a-results.yml",
    "bundesliga-live-cycle.yml",
    "bundesliga-results.yml",
    "ligue1-live-cycle.yml",
    "ligue1-results.yml",
    "eredivisie-live-cycle.yml",
)

PROVIDER_FREE_RESULTS_WORKFLOWS = (
    "serie-a-results.yml",
    "bundesliga-results.yml",
    "ligue1-results.yml",
)

PAID_MANUAL_ONLY_WORKFLOWS = (
    "odds-snapshots.yml",
    "la-liga-live-cycle.yml",
    "rpl-odds-snapshots.yml",
    "rpl-results.yml",
    "serie-a-odds-snapshots.yml",
    "bundesliga-odds-snapshots.yml",
    "ligue1-odds-snapshots.yml",
    "eredivisie-odds-snapshots.yml",
    "eredivisie-results.yml",
    "turkey-portugal-market-only-cycle.yml",
    "multi-market-coverage-audit.yml",
)


def _crons(path: Path) -> list[str]:
    source = path.read_text()
    return re.findall(r'cron:\s*["\']([^"\']+)["\']', source)


def _cron(path: Path) -> str:
    matches = _crons(path)
    assert len(matches) == 1, f"Expected one scheduled cron in {path.name}: {matches}"
    return matches[0]


def _expand_field(field: str, maximum: int) -> set[int]:
    if field == "*":
        return set(range(maximum))
    if field.startswith("*/"):
        step = int(field[2:])
        return set(range(0, maximum, step))
    values = {int(value) for value in field.split(",")}
    assert all(0 <= value < maximum for value in values)
    return values


def _slots(cron: str) -> set[tuple[int, int]]:
    minute, hour, day_of_month, month, day_of_week = cron.split()
    assert day_of_month == "*"
    assert month == "*"
    assert day_of_week == "*"
    minutes = _expand_field(minute, 60)
    hours = _expand_field(hour, 24)
    return {(hour_value, minute_value) for hour_value in hours for minute_value in minutes}


def test_operational_scheduled_workflows_do_not_share_utc_slots():
    schedules = {
        name: _slots(_cron(WORKFLOW_DIR / name))
        for name in SCHEDULED_OPERATIONAL_WORKFLOWS
    }

    collisions = []
    names = list(schedules)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = schedules[left] & schedules[right]
            if overlap:
                collisions.append((left, right, sorted(overlap)))

    assert collisions == []


def test_paid_workflows_are_manual_only():
    for name in PAID_MANUAL_ONLY_WORKFLOWS:
        source = (WORKFLOW_DIR / name).read_text()
        assert "workflow_dispatch:" in source, name
        assert _crons(WORKFLOW_DIR / name) == [], name
        assert "push:" not in source, name


def test_provider_free_results_are_scheduled_without_odds_api_secret():
    for name in PROVIDER_FREE_RESULTS_WORKFLOWS:
        path = WORKFLOW_DIR / name
        source = path.read_text()
        assert "workflow_dispatch:" in source, name
        assert len(_crons(path)) == 1, name
        assert "THE_ODDS_API_KEY" not in source, name
        assert "update_" in source and "_results.py --write" in source, name

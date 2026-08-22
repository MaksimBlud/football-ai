"""Run research-only Challenger shadow monitoring after a successful step."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence


SHADOW_SCRIPT = "generate_upcoming_challenger_shadow.py"


def run_with_shadow(
    upstream_command: Sequence[str],
    *,
    runner: Callable = subprocess.run,
) -> int:
    """Run shadow generation only when ``upstream_command`` succeeds."""

    upstream = runner(
        [
            sys.executable,
            *upstream_command,
        ],
        check=False,
    )

    if upstream.returncode != 0:
        print(
            "Upstream step failed; Challenger shadow generation skipped "
            f"(exit code {upstream.returncode})."
        )

        return upstream.returncode

    print()

    print(
        "Upstream step succeeded; running research-only "
        "Challenger shadow generation..."
    )

    shadow = runner(
        [
            sys.executable,
            SHADOW_SCRIPT,
        ],
        check=False,
    )

    if shadow.returncode != 0:
        print(
            "WARNING: Challenger shadow generation failed "
            f"(exit code {shadow.returncode}); the successful odds "
            "snapshot is unaffected."
        )

    return 0

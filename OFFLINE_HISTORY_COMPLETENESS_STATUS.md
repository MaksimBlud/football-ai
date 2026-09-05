# Offline History Completeness

Research-only historical validation now derives season completeness from the number of participating teams instead of assuming a 20-team, 380-match league.

For a standard double round-robin season with `N` teams, the expected fixture count is `N * (N - 1)`. Validation also requires each ordered home/away pairing exactly once.

This supports historical league-size changes such as 20 teams (380 matches), 18 teams (306 matches), and 16 teams (240 matches) without weakening completeness checks.

No production model artifacts, runtime activation, odds collection, or Supabase writes are changed by this block.

## Research checkpoint

**Finding:** The V1 protocol and primary statistic are clearly documented, providing a concrete target for replication.

**Evidence:** Read research/CROSS_MARKET_LEAD_LAG_V1.md which defines the primary statistic `alignment_dot = dot(lead, move)`, the lead vector as synthetic 1X2 minus opening 1X2, and the permutation null (10,000 within-league-season permutations). This establishes the exact metric and null method that must be replicated for Bundesliga and Ligue 1.

**Next action:** Fetch Bundesliga and Ligue 1 CSV files from the pinned GitHub mirrors and verify that they contain the required Bet365 fields (B365H, B365D, B365A, B365>2.5, B365<2.5, AHh, B365AH, B365AHH, B365AHA, B365CH, B365CD, B365CA) and that half‑goal handicap lines are present.


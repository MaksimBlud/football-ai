# OU25_CLOSING_MOVEMENT_V1 execution boundary

This note is committed **before** the first aggregate validation/OOT market-movement metrics are opened.

- Contract: `research/OU25_CLOSING_MOVEMENT_V1.md`
- Runner: `ou25_closing_movement_v1.py`
- Focused tests: `tests/test_ou25_closing_movement_v1.py`
- Dedicated CI: `.github/workflows/ou25-closing-movement-v1.yml`
- Base main: `b342d34ae5f029fcf02716dda111abd5d1e1cac4`
- No aggregate movement result has been inspected at this point.
- `NO_BET`, research-only, no production model mutation, no paid provider request, no Supabase write.

Any implementation defect discovered by CI may be corrected only without changing the frozen target, feature set, estimator, temporal split, provider priority, metrics, or gate.

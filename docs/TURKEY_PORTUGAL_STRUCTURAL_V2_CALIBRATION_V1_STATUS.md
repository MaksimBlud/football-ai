# Turkey / Portugal Structural V2 Calibration V1 — Status

Status: **PREREGISTERED / NOT YET EVALUATED / RESEARCH-ONLY**

The calibration protocol is frozen in `research/turkey_portugal_structural_v2_calibration_v1.json` before any outcome-dependent candidate selection is run.

The research is independent for `TURKEY_SUPER_LIG` and `PRIMEIRA_LIGA`. Final parameters from EPL or any other league must not be copied. Cross-league pooling is prohibited.

Historical source readiness has been established outcome-blind for completed seasons 2016/17 through 2025/26. The frozen 1X2 market source for both leagues is BET365 (`B365H/B365D/B365A`). Current season 2026/27 is excluded.

Outcome-dependent evaluation is not allowed until this preregistration is merged to `main`. After that gate, evaluation must follow the frozen nested season walk-forward protocol exactly. A negative result or MARKET_ONLY fallback is a valid outcome.

This research cannot activate Structural V2, cannot mutate Turkey/Portugal runtime calibration fields, cannot promote a model, and cannot modify production `.pkl` artifacts. Any future runtime calibration requires a separate explicit review and PR.

# RPL Safety Boundary

The RPL operational block is research-only and MARKET_ONLY.

Production artifacts are outside this pipeline. No RPL operational module may load, train, overwrite, or promote production `.pkl` models. Structural V2 remains disabled until a separate calibrated research phase explicitly passes its gate.

Durable writes are limited to league-scoped odds snapshots, immutable research observations, canonical prediction-ledger rows, and immutable finished results.

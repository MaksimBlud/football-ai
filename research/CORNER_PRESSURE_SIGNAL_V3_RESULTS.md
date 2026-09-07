# CORNER_PRESSURE_SIGNAL_V3 — Results

Status: **HISTORICAL PRIMARY RESULT COMPLETE / NOT_PORTABLE_PRESSURE_DISCRIMINATOR**

## Primary result: all shots

| Season | Matches | AUC >9.5 | Pearson corr with total corners |
|---|---:|---:|---:|
| 2019/2020 | 351 | 0.504832 | 0.086568 |
| 2020/2021 | 370 | 0.498051 | 0.056654 |
| 2021/2022 | 370 | 0.455471 | -0.062212 |
| 2022/2023 | 370 | 0.470137 | 0.023179 |
| 2023/2024 | 370 | 0.524756 | 0.183394 |
| 2024/2025 | 370 | 0.543075 | 0.102563 |
| 2025/2026 | 380 | 0.492663 | 0.056097 |

Across 2581 held-out matches:
- weighted primary AUC = **0.498357**;
- seasons with AUC > 0.50 = **3/7**.

Frozen primary decision: **NOT_PORTABLE_PRESSURE_DISCRIMINATOR**.

The preregistered success rule required weighted AUC > 0.52 and at least 5/7 positive seasons. Neither condition passed.

## Secondary result: shots on target

The secondary diagnostic was fixed before evaluation and cannot replace the primary signal.

Across the same 2581 held-out matches:
- weighted AUC = **0.512793**;
- AUC > 0.50 in **5/7 seasons**.

This is more promising than all shots but still below the preregistered 0.52 strength threshold.

## Interpretation

Simple attacking-volume pressure is not a stable standalone discriminator of Over 9.5 corners. The relationship is strongly season-dependent.

Shots on target contain a little more ranking information, but the effect is still too weak to declare a portable betting-style signal.

This does not invalidate V2's small improvement in expected numerical corner count. V2 and V3 answer different questions:
- V2: can we slightly improve the expected number of corners? Yes, after heavy shrinkage.
- V3: can we reliably rank high-corner vs low-corner matches using pressure alone? No.

## Next permitted step

One final historical free-data experiment is justified: combine the already studied corner-state and pressure information in a fixed walk-forward classifier trained only on seasons earlier than each held-out season.

That combined experiment must be preregistered separately and treated as adaptive/sequential historical evidence, not as a brand-new independent confirmation.

If the combined experiment also fails to produce meaningful stable discrimination, the next real information source is bookmaker corner-market data or richer football event data, neither of which is available for free in the current historical store.

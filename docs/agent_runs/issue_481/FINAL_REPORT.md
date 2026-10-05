# Research V5 final report — Issue #481

## Вывод простым языком

Диагностика 2024/25 выполнена полностью deterministic Python без LLM/API.
Итог: **NO_OBSERVABLE_SOURCE_MARKET_EXPLANATION**.

В 2024/25 не найден широкий source/schema, AH-composition, bookmaker-margin или structural-magnitude сдвиг, который одинаково проявляется минимум в 4/5 лигах. Поэтому ослабление alignment нельзя честно объяснить наблюдаемой общей сменой источника/рынка.

Formal V1/V2 decisions remain unchanged. Это не betting signal и не разрешение на
production/promotion или paid collection.

## Technical appendix

Result: `research/agent_runs/issue_481/RESULT.json`.
Rows: 2920. Diagnostic families: coverage/schema, AH composition, overround,
structural magnitudes, league/sample composition. Outcome-free; no 2026/27; no paid API;
no Supabase; no production operation.

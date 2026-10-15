# Signal Scout — 2026-10-15 — Polymarket football exchange: five-league source and PIT gate

**Decision:** `IDEA / WAITING_BY_API_PIT_BOOKMAKER_AND_LIQUIDITY`. No candidate Issue; no Research Brain transfer; no outcomes read or tested; no production/Supabase/paid API operations.

## Mandatory repository-first audit

Fresh GitHub `main` SHA: `328bc3966c657976908acdce94809a11fdd18a24` (verified by GitHub main...main comparison). Read `research/programs/registry.json` (14 programs: 13 `PROGRAM_DONE`, 1 `BLOCKED`), `PROJECT_CONTINUITY.md`, existing Scout reports and open GitHub issues. Targeted Issue/code searches for `Polymarket`, `Kalshi`, `liquidity`, `crowd` found no matching named research candidate. **Absence from search is not proof of exhaustive independence.**

Binding nearby completed families:
- `bookmaker_market_microstructure_1_price_formation` / Issues #532, #553: bookmaker-specific Bet365/Pinnacle repricing; PROGRAM_DONE. Do not reopen or reuse its opened OOT.
- `independent_information_source_disagreement` / Issue #568: *football-only* Understat estimate vs bookmaker consensus, failed frozen OOT; PROGRAM_DONE. No threshold, side, league or model retuning.
- `cross_market_lead_lag` / Issues #481/#482 and `multi_market_repricing_state` / #573: rejected cross-market repricing mechanisms, PROGRAM_DONE.
- `point_in_time_snapshot_cadence` / #594: blocked for lack of bookmaker PIT snapshots. Polymarket quotes are NOT The Odds API/bookmaker snapshots and do not automatically remove that block.

## One preliminary, mechanistically distinct direction (not a discovered signal)

`CROWD_EXCHANGE_VS_BOOKMAKER_1X2_V0`: at a fixed pre-kickoff decision time, *independent prediction-exchange crowd* 1X2 prices may contain information not fully reflected in a conventional bookmaker's fair 1X2 vector. Distinct participant venue and order-book mechanism are the hypothesised cause, NOT proof of informational independence. This is **not** a football-only tactical probability model, not a bookmaker-vs-bookmaker margin transform, and not a revival of any failed historical statistic. It still overlaps the general concept of probability disagreement; Research Brain must rule on family independence before admission.

Exact *proposed, not frozen* features for fixture `f` at `asof = kickoff_utc - 24h`:
1. `exchange_p_home/asof`, `exchange_p_draw/asof`, `exchange_p_away/asof` from the correct **regulation-time** three-outcome contract, each with its own CLOB outcome token ID and latest valid observation timestamp `<=asof`; missing remains missing.
2. `exchange_bookmaker_log_ratio_vector`: log ratios of normalized exchange probabilities to a fixed preregistered same-time bookmaker fair 1X2 vector; no retrospective closing prices or outcome-conditioned thresholds.
3. Quality/provenance fields: token ID, event/market ID, event scheduled kickoff, market opening, first seen time, actual price timestamp, observation age, best bid/ask, spread, outcome-specific matched volume and market volume, active status and rule text. **Price is not automatically executable or fair probability.**
4. `liquidity_missing` and `wide_spread` diagnostics only until Research Brain freezes eligibility. No post-hoc exclusion based on results.

## Actual public source evidence (outcome-free)

**Official source/API documentation**:
- Polymarket official market-data guide: https://github.com/Polymarket/agent-skills/blob/main/market-data.md . Gamma public event/market discovery; CLOB public read-only orderbooks, prices and historical `{t,p}` series; no API key for reads. The guide states that when bid/ask spread exceeds **$0.10**, the UI may show *last trade price rather than midpoint* — a serious source-definition pitfall.
- Polymarket Institute public data guide: https://institute.polymarket.com/data . Token IDs must be resolved via Gamma; CLOB price-history is not a historical order book.

**Direct public football-market pages**, containing named home/draw/away quotes, were located for each of the five major leagues (five **league-page presences**, not verified season-long fixture coverage):
- EPL: https://polymarket.com/sports/epl/games — page lists 10 future Oct 17–19, 2026 matches with 1X2 labels; these are future fixtures, not outcomes.
- La Liga: https://polymarket.com/sports/laliga/games — future Oct 16–19 matches and three 1X2 outcomes.
- Bundesliga: https://polymarket.com/sports/bundesliga/games — future Oct 16–17 matches and three outcomes.
- Ligue 1: https://polymarket.com/sports/ligue-1/games — future October matches and three outcomes.
- Serie A: https://polymarket.com/sports/sea/sea-rom-gen-2026-10-17 — Roma–Genoa Oct 17 regulation-time 1X2 shown. **Critical false-positive:** one previously crawled version of this page showed `$0` *moneyline* traded volume despite displayed 1X2 prices. A displayed price alone is NOT evidence of a liquid or freshly observed market. This is a historical page observation, not a claim about current liquidity.

**Limits of this cycle's live verification:** attempted read-only Gamma event endpoint `https://gamma-api.polymarket.com/events/slug/epl-mac-ips-2026-10-17` via web: inaccessible. A direct read-only Python HTTPS attempt failed DNS resolution. Therefore **zero actual Gamma token-ID payloads, zero actual CLOB historical points, zero verified per-outcome quote_observed_at timestamps, and zero matched bookmaker T-24h quotes** were obtained. No invented 10/10 *API* coverage, no historical liquidity claims, and no live prices archived. Search-crawled web prices are not a valid timestamped as-of record. Legal/redistribution rights for a commercial Football AI product remain unverified.

## Strict outcome-free feasibility gate before any candidate Issue

1. Enumerate *all* fixtures in a predeclared five-league chronological universe independently of exchange coverage. Do not sample only liquid or resolved matches; do not inspect protected 2026/27 outcomes.
2. Retrieve permitted free Gamma event/market metadata, correct regulation-time home/draw/away token IDs, rule versions, kickoff and market-open timestamps. Prove that the markets were open and the rules matched at each `kickoff-24h` cutoff.
3. Retrieve public CLOB price history for each of the **three** tokens. Check `t<=asof` for each, independently verify history is genuine past-observed data (not a retrospective rewrite or interpolation), inspect gaps, token mapping, zero trades, stale/last-trade price, spread and volume. Produce coverage and missingness by league/season, *without outcomes*. No post-hoc liquidity cutoff.
4. Obtain **same-match, same-asof independently observed bookmaker 1X2 quotes** and a fixed fair-probability transform. Football-Data opening/closing columns without quote observation timestamps are NOT acceptable T-24h replacements. If this is unavailable, `BLOCKED_BY_MARKET_PIT`.
5. Check lawful terms and publication/redistribution rights for both datasets. Verify enough independent liquid observations over multiple seasons for chronological validation and genuinely untouched OOT. Do not borrow protected 2026/27 V2 outcomes.
6. Only Research Brain can decide nonduplication, freeze the exact features, as-of horizon, liquidity/missingness rule, matched universe, market-only baseline, market-plus-exchange model and exchange-only diagnostic. Evaluate paired multiclass Brier and LogLoss on frozen validation and independent untouched OOT, fixture-cluster/league-stratified CIs and league stability. No Scout outcome tests.
7. Negative controls: swap exchange prices between fixtures in the same prespecified kickoff window; use unrelated event tokens; zero-volume/wide-spread controls; post-cutoff values must be rejected; placebo bookmaker-vs-bookmaker transform must not be relabelled independent; demonstrate sensitivity to exchange quote staleness and cancellation rules.
8. **STOP** on missing token/time provenance, inadequate lawful coverage, missing same-time bookmaker baseline, overlapping completed family, unstable validation/OOT or any failed prespecified gate. **SUCCESS** only after Brain's independently frozen OOT shows both Brier and LogLoss improvements with uncertainty and stability criteria. Never infer betting profit, executable fills or promotion from UI quotes.

## Cycle / 24h audit

Four independently verified previous Scout report commits in the preceding ~10h:
- 2026-10-14 20:15:37Z `abbb4a07ea535e1b7b1de6d761d7f16cc2e68dc4` (TipsAudit source gate)
- 2026-10-14 22:16:57Z `8e60cce4bebad110a17b52b84888adc701c71827` (referee PIT gate)
- 2026-10-15 01:21:12Z `b37031bacc2dc8fbd8a7cbc54ac47987dfe02399` (manager suspension gate)
- 2026-10-15 05:21:40Z `57961a7ffcafd3bc35c65d5728c95539f97f56df` (cup extra-time rule gate)

These are reports, **not** four admitted hypotheses. The preceding reports record **zero** Research Brain candidate transfers. Exact prior run start/end durations were not independently instrumented, so 40-minute cycle productivity cannot be inferred from commit timestamps. This cycle: one new source-family direction screened; five league page presences found; **0 DATA_FEASIBLE**, **0 admitted independent candidates**, **0 candidate Issues**, **0 Research Brain handoffs**, **0 outcome tests**, **0 paid API requests**, **0 Supabase/production changes**.

**Next only if access allows:** independently prove three-token Gamma+CLOB `T-24h` history on a fixed future fixture universe, then verify matched bookmaker quote timestamps. Otherwise keep WAITING; do not manufacture another Issue.

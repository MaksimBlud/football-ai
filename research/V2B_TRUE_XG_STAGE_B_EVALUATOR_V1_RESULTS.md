# V2B TRUE XG STAGE-B EVALUATOR V1 — Results

Status: **FINAL OPENED-SAMPLE HYPOTHESIS GENERATION / WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS**

## Provenance

Workflow run:

`36443401120`

Authoritative evaluator artifact:

- ID `10978848942`;
- digest `sha256:966521425bbed4a589e6e1c9b59d335b519ce2a0cd7784724f895c2e64d6358c`;
- size 4,985 bytes.

Frozen true-xG Stage-B source:

- artifact `10979252403`;
- digest `sha256:b5372b78a0d78b20cb921a79cf1a0e4e82211f8cc70cfe9b396cb0e11689b880`;
- eligible fixture hash
  `sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`;
- feature hash
  `sha256:f4128f41a541788a4690bd8f1065cef468622494fe56de2a561a4ba07b59b0a5`;
- frozen calls = 30 UP / 4 DOWN.

Market source:

- artifact `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`.

No provider request occurred during evaluation.

## Observed V2B movement

Evaluated rows:

**34**

Observed movement:

- UP = **7**;
- DOWN = **3**;
- ZERO = **24**.

Direction-comparable rows:

**10**

## Raw frozen-rule concordance

Concordant:

**7 / 10 = 0.70**

On raw hit rate alone this looks positive, but the frozen call distribution is highly
imbalanced.

Among the 10 non-zero movers:

- observed UP = 7;
- observed DOWN = 3.

The constant majority-direction rule:

`always UP`

therefore also achieves:

**7 / 10 = 0.70**

Stage-B excess concordance over constant-UP:

**0.00**

## Direction discrimination

All 10 non-zero comparable rows received the frozen call:

**UP**

The four frozen DOWN calls all occurred on ZERO-movement rows.

Therefore:

- UP recall = **1.00**;
- DOWN recall = **0.00**;
- balanced direction accuracy = **0.50**.

This is the key reason the 70% raw concordance is not evidence of useful direction
discrimination.

## Call-group movement

Frozen UP calls:

- rows = 30;
- zero movement = 20;
- mean centre_delta = **+0.100144**;
- median centre_delta = 0.

Frozen DOWN calls:

- rows = 4;
- zero movement = 4;
- mean centre_delta = **0.000000**;
- median centre_delta = 0.

The frozen consistency condition required the DOWN group mean to be negative.

It was not.

## By-league diagnostics

- Bundesliga: 2/2 = **1.00**;
- EPL: 0/2 = **0.00**;
- La Liga: 2/2 = **1.00**;
- Ligue 1: 0/1 = **0.00**;
- Serie A: 3/3 = **1.00**.

Leagues with >=2 comparable rows and concordance >0.50:

**3**

This condition passes, but it does not overcome the failed DOWN-group sign condition
or the lack of discrimination beyond always-UP.

## Continuous relationship

Frozen xG Stage-B score vs centre_delta:

- Pearson = **+0.325976**;
- Spearman = **+0.097325**.

The rank relationship is weak.

## Final classification

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

The frozen mapping is not a useful portable direction discriminator on V2B.

The 70% raw concordance must not be reported as a 70% predictive edge because:

1. the same 70% is achieved by always predicting UP among non-zero movers;
2. all comparable xG calls are UP;
3. DOWN recall is 0%;
4. balanced accuracy is 50%;
5. frozen DOWN calls have zero mean movement rather than negative movement.

## Binding conclusion

Close the exact mapping:

`POOLED_2025_NPXG_ENVIRONMENT_SIGN_V1`

Do not:

- move the previous-season baseline;
- use league-specific baselines;
- rebalance the 30/4 calls;
- change npxG weights;
- switch to raw xG after seeing this result;
- change the five-match horizon;
- exclude EPL or Ligue 1;
- add a post-hoc FAIR_CENTRE threshold;
- describe 7/10 as a confirmed edge.

The richer true-xG source remains useful as football information, but this simple
absolute-environment direction mapping did not produce discrimination beyond a trivial
constant-UP rule.

## Next research implication

Reliable individual corner-market direction is still unresolved.

Another Stage-B mechanism should be considered only if it introduces a genuinely new,
point-in-time information dimension rather than another same-sample transformation of:

- CORNERS10;
- SHOTS10;
- result/Elo residuals;
- this absolute true-xG environment mapping;
- FAIR_CENTRE direction.

Promising source families must first pass source/time-provenance feasibility.

## Safety

- research-only;
- opened-sample hypothesis generation only;
- NO_BET;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.

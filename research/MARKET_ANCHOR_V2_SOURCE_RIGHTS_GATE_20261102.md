# Original V2 recovery — source-rights gate (2026-11-02; manifest reconciled 2026-11-05)

## Decision

The frozen candidate may be used only for noncommercial, frozen-weight personal/academic research inference under the project's narrow operational interpretation of the provider policy. This is **not** a provider-issued AI-inference licence.

AI model training, refitting/replay from the provider's data, commercial use, and public-product publication remain blocked. A GitHub artifact digest, source CSV hash, source-before-quote timestamp, or successful CI run proves integrity/provenance; none grants data-use rights.

## Official provider policy checked on 2026-11-03

Football-Data.co.uk's official fair-data-usage policy says its free CSV/Excel data are intended for private individuals' personal betting or academic research, with manual or light automated downloading (maximum twice per week). It says the data are not intended for commercial or AI data-training projects.

Source: https://football-data.co.uk/contact.php

The policy does not expressly define frozen-weight AI inference. The project therefore treats only noncommercial personal/academic inference with the already frozen candidate, no fitting/refitting/selection, and no public publication as within the narrow research scope. This interpretation is not a provider-issued AI-inference licence.

## Current manifest state — exact values

`research/source_rights/football_data_co_uk.json` records:

- `rights_status = CONDITIONAL_RESEARCH_ONLY`;
- `research_use_permitted = true`;
- `research_inference_permitted = true`;
- `research_inference_scope = PERSONAL_BETTING_OR_ACADEMIC_RESEARCH_ONLY`;
- `ai_model_training_permitted = false`;
- `commercial_use_permitted = false`;
- `public_product_use_permitted = false`;
- `max_automated_download_sessions_per_week = 2`;
- `authorization = null`.

The previous `rights_status = NOT_GRANTED` wording was inaccurate for the overall manifest. The precise restriction is that **AI model-training permission is not granted**; conditional personal/academic research inference is separately permitted by the project's operational interpretation.

## Recovery gate

`market_anchor_v2_training_archive.py` calls `require_ai_model_training_permission()` before GitHub artifact discovery, listing, download, extraction, or replay. That function requires `rights_status = GRANTED`, an explicit authorization, and SHA-pinned evidence covering both AI training and noncommercial research. The current manifest has no authorization and explicitly sets `ai_model_training_permitted = false`; therefore the historical training-archive recovery path must fail closed before artifact I/O.

Do not dispatch candidate reconstruction/replay under the current rights state. The already frozen candidate can be runtime-attested without training; this recovery workflow's manual training-input path is not authorized.

## Download budget

The manifest allows at most two automated source-download sessions per rolling seven days. A technical GitHub Actions budget guard does not create provider permission and does not cure prior overuse. Do not initiate additional source downloads while the observed usage exceeds the stated limit or while the provider's conditions are unresolved.

## Scope and safety

- No new Football-Data request was made by this rights-gate change.
- No paid provider request was made.
- No Supabase read/write/DDL is needed for the rights decision.
- No protected 2026/27 target outcomes are read.
- Original V2 features, weights, candidate SHA, lambdas, stability gate, and 30-event outcome gate are unchanged.
- No candidate refit/replay is authorized by this manifest.
- The rights gate distinguishes frozen-weight personal/academic inference from training, commercial use, and public-product publication.

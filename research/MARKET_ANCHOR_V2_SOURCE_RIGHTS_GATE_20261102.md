# Original V2 recovery — source-rights gate (2026-11-02)

## Decision

The historical archive recovery path is blocked until explicit permission for AI model training is documented. A GitHub artifact digest, source CSV hash, source-before-quote timestamp, or successful CI run proves integrity and provenance; none of those proves a right to use the data for model training.

## Official provider policy checked on 2026-11-02

Football-Data.co.uk's official fair-data-usage policy says its free CSV/Excel data are intended for private individuals' personal betting or academic research, with manual or light automated downloading (maximum twice per week). It explicitly says the free data are not intended for commercial or AI data-training projects and says users should assume no data-use permission is granted for such projects.

Source: https://football-data.co.uk/contact.php

## Current manifest state

`research/source_rights/football_data_co_uk.json` records:

- `rights_status = NOT_GRANTED`;
- `ai_model_training_permitted = false`;
- no authorization document;
- no evidence SHA for a permission grant.

Therefore `market_anchor_v2_training_archive.py` must fail before any GitHub artifact listing, download, extraction, or training replay. The existing archive is not to be treated as an authorized training input.

## Unlock requirements

A future change may set the status to `GRANTED` only after an actual written permission or a source license explicitly covering both `AI_MODEL_TRAINING` and `NONCOMMERCIAL_RESEARCH` is added as a local evidence file. The manifest must bind that file by SHA-256, identify the rights holder and license, record a reviewer and explicit UTC validity interval, and point to a direct HTTPS evidence URL. Synthetic test grants are test-only and are never stored as production authorization.

Commercial use remains a separate permission question. This gate does not grant commercial rights.

## Scope and safety

- No new Football-Data request was made by this change.
- No paid provider request was made.
- No Supabase read/write/DDL was needed.
- No protected 2026/27 outcomes were read.
- Original V2 features, weights, candidate SHA, lambdas, stability gate, and 30-event outcome gate are unchanged.
- The source-rights gate applies to historical training/recovery; it does not claim that an open results-only source can replace the frozen 19-feature training dataset.

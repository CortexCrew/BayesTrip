# DESIGN

This document records the exact formulas and data sources used to build
`BayesTrip_Data.xlsx`, so every number in the workbook is traceable to
either a deterministic formula or a cited piece of evidence.

## Data sources

| Purpose | Source | Notes |
|---|---|---|
| Geocoding (lat/lng) | OSM Nominatim | Free, no key required |
| Popularity signal | OpenTripMap API | `rate` (importance 1-7h) + Wikipedia extract, per place |
| Travel time (point-to-point) | OSRM public routing API | Driving profile, free, no key required |
| Opening hours | Overpass API (OSM `opening_hours` tag), web research fallback | Fallback logged in 08_Evidence |
| Qualitative attributes (CPT) | Wikipedia, official tourism sites, travel guides | Extracted via structured JSON, see below |

## 02_BN_Prior — formula

*To be finalized when step 3 is implemented; will combine OpenTripMap's
`rate` field with a log-scaled popularity term, normalized to sum to 1
across all 20 places.*

## 03_BN_CPT — process

For each place and each evidence variable, 2-3 sources are read and an
LLM extraction step produces structured rows:
`place_id, variable, state, evidence_text, justification, source_url`.
The `justification` field distinguishes an explicit source claim
("source states X") from an inference drawn from a general description
("inferred from description") — it never invents a citation for a
number the source did not give. A separate, deterministic normalization
pass (plain code) then rescales each place's per-variable values to sum
to 1. No LLM output is treated as final without that normalization pass.

## 04_HMM_Initial / 05_HMM_Transition — formula

`score = 1 / travel_time_seconds`, normalized (initial: sum to 1 across
all places; transition: each row sums to 1 across all destinations).

## 06_HMM_Emission — formula

Per place x {Morning, Afternoon, Evening}: 1.0 if fully open in that
slot, 0.5 if partially open, 0.02 floor if closed (never a hard 0, so a
state is never permanently zeroed out in Viterbi). Normalized per place
across the 3 slots to sum to 1.

## Validation

`09_Validation` re-derives every sum programmatically and reports
PASS/FAIL per check; it does not re-trust any upstream normalization.

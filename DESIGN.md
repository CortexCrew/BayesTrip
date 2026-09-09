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

For each place, OpenTripMap's `places/radius` endpoint is queried
around its already-geocoded coordinate to find the matching POI (exact
or substring name match, else the nearest result) and read its `rate`
field -- OpenTripMap's own POI-notability scale, 0-3 numeric plus a
1h/2h/3h/7h tier for globally significant places. `rate` is mapped onto
a single 0-7 ordinal score and normalized across all 20 places to sum
to 1. Deterministic once `rate` is fetched; the only judgment call is
picking the right POI out of the radius search results, which is
logged per place in 08_Evidence either way.

Pending: requires the OPENTRIPMAP_API_KEY environment variable
(step03_bn_prior.py is implemented and ready to run once a key is
available, but has not yet been executed).

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

Time slots are fixed as Morning 06:00-12:00, Afternoon 12:00-17:00,
Evening 17:00-21:00. Opening hours were researched per place (free
text + sources in `raw/opening_hours_research.json`) and hand-extracted
into structured daily intervals (`raw/opening_hours.json`); day-of-week
variation (e.g. a Tuesday closure) is not modeled since the table only
covers time-of-day within a visiting day.

Per place x slot: 1.0 if the slot is fully covered by an open interval,
0.5 if partially covered, 0.02 floor if not covered at all (never a
hard 0, so a state is never permanently zeroed out in Viterbi).
Normalized per place across the 3 slots to sum to 1.

## Validation

`09_Validation` re-derives every sum programmatically and reports
PASS/FAIL per check; it does not re-trust any upstream normalization.

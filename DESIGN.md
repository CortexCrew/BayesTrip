# DESIGN

This document records the exact formulas and data sources used to build
`BayesTrip_Data.xlsx`, so every number in the workbook is traceable to
either a deterministic formula or a cited piece of evidence.

## Data sources

| Purpose | Source | Notes |
|---|---|---|
| Geocoding (lat/lng, address) | Geoapify Geocoding API | Replaced OSM Nominatim; see step02_coordinates.py |
| Popularity signal | Web research (Tripadvisor preferred, documented fallback otherwise) | Rating + review count, per place |
| Travel time (point-to-point) | OSRM public routing API | Driving profile, free, no key required |
| Opening hours | Overpass API (OSM `opening_hours` tag), web research fallback | Fallback logged in 08_Evidence |
| Qualitative attributes (CPT) | Wikipedia, official tourism sites, travel guides | Extracted via structured JSON, see below |

## 02_BN_Prior — formula

OpenTripMap (originally planned for both coordinates and popularity) is
blocked (account email verification issue) and has been dropped
entirely from this table -- Geoapify is not a substitute for popularity
either, since it has no rating/review signal. Instead, popularity
evidence (rating, review count) is gathered by a research pass: web
search, preferring Tripadvisor's publicly visible rating/review count
where a normal search/page-load surfaces it (no scraping, no bypassing
paywalls or access restrictions), falling back to another reliable
source (Holidify, Justdial, TripHobo, etc.) when Tripadvisor isn't
accessible that way, with the fallback explicitly recorded. If no
numeric rating/review count can be found anywhere, the fields are left
null rather than invented -- raw evidence in
`raw/popularity_research.json`.

The research pass never computes a score. This is the separate,
deterministic scoring pass, run over that raw evidence:

```
popularity_score_i =
    rating_i * ln(review_count_i + 1)   if both rating_i and review_count_i are known
    rating_i                             if only rating_i is known (no review-count multiplier --
                                          NOT treated as review_count=1, which would silently
                                          invent a number)
    FLOOR_SCORE (= 1.0)                  if neither is known, so a place with no popularity
                                          evidence still gets a small nonzero prior instead of
                                          being zeroed out of the recommendation entirely
```

`P(place_i) = popularity_score_i / sum(popularity_score_all_places)`,
normalized across all 20 places to sum to 1. The `ln(review_count + 1)`
term rewards places with more reviews but with diminishing returns
(a place with 50,000 reviews isn't treated as 50x "more popular" than
one with 1,000); ratings are typically on a 0-5 scale across sources,
so `rating * ln(review_count + 1)` keeps quality and volume on a
comparable footing without either dominating. FLOOR_SCORE is a fixed,
documented code constant -- not a fabricated rating -- applied only
when no popularity evidence exists at all.

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

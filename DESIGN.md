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

## 04_HMM_Initial — formula

pi(place) represents first-stop *accessibility* from a fixed starting
location (Chennai Central Railway Station), not destination popularity
-- that is 02_BN_Prior's job (P(Place)); the two are deliberately kept
separate and this step never reads the BN prior.

Coordinates come exclusively from 07_Coordinates (Geoapify Geocoding
API, the finalized coordinate source for this project -- the old OSM
Nominatim data is no longer used anywhere). Road distance and travel
time from Chennai Central to each place are both read from the same
OSRM public routing table service response, so distance and time are
never silently mixed from different sources (e.g. straight-line vs.
road).

```
raw_accessibility_score_i = 1 / (travel_time_min_i + EPSILON)   [EPSILON = 0.01 min]
pi_i = raw_accessibility_score_i / sum_j(raw_accessibility_score_j)
```

Deterministic once travel times are fetched; if OSRM cannot find a
route to a place, no value is fabricated -- that place is excluded
from the normalization and flagged `needs_manual_review` rather than
assigned an invented probability.

## 05_HMM_Transition — formula

A[i][j] = P(S_t = place_j | S_(t-1) = place_i): the probability of
moving to place_j immediately after visiting place_i, based on travel
accessibility between the two -- distinct from 02_BN_Prior (popularity)
and 04_HMM_Initial (first-stop accessibility from Chennai Central);
this table never reads either.

Coordinates come exclusively from 07_Coordinates (Geoapify). Self-
transitions (place_i -> place_i) are excluded, matching this project's
existing policy from the original wide-format implementation (which
set A[i][i] = 0), so the table has 20 x 19 = 380 rows, one per ordered
pair of distinct places. Distance and travel time for all pairs come
from a single OSRM table-service call (`distance_duration_matrix`,
shared with 04_HMM_Initial).

```
raw_transition_score(i, j) = 1 / (travel_time_min(i, j) + EPSILON)   [EPSILON = 0.01 min]
transition_probability(i, j) = raw_transition_score(i, j) / sum_k(raw_transition_score(i, k))
```

normalized independently per from_id (over its 19 to_places), never
across the full 380-row table at once. If OSRM cannot route a pair, no
value is fabricated -- that pair is excluded from its from_id's
normalization and flagged `needs_manual_review`.

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

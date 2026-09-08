# BayesTrip

A tourist recommendation system for Chennai. A Bayesian Network over 20
destinations, conditioned on visitor evidence (Age, Budget, Interest,
Travel Type, Weather), produces a posterior P(Place | Evidence). The
Top-5 places are then sequenced into a same-day itinerary using a
Hidden Markov Model (hidden state = place, observations = time-of-day
slots) solved with the Viterbi algorithm, and displayed on a map.

## Project layout

```
data_generation/       Scripts that build BayesTrip_Data.xlsx, one module per table
recommendation_engine/ Bayesian inference + HMM/Viterbi, consumes the workbook
data/                  Generated BayesTrip_Data.xlsx output
DESIGN.md              Data sources, formulas, and normalization rules
```

## Pipeline (data generation)

| # | Table | Source |
|---|-------|--------|
| 1 | 01_Place_Master | Fixed list of 20 Chennai places |
| 2 | 07_Coordinates | OSM Nominatim geocoding |
| 3 | 02_BN_Prior | OpenTripMap popularity (rate + Wikipedia extract) |
| 4 | 03_BN_CPT | Web research + structured extraction, deterministic normalization |
| 5 | 04_HMM_Initial | OSRM travel time from Chennai Central |
| 6 | 05_HMM_Transition | OSRM pairwise travel time, 20x20 |
| 7 | 06_HMM_Emission | Overpass opening_hours + web research fallback |
| 8 | 08_Evidence | Provenance log for every fact used above |
| 9 | 09_Validation | Automated PASS/FAIL checks on all normalizations |

See [DESIGN.md](DESIGN.md) for exact formulas and data source details.

## Recommendation engine

`recommendation_engine/` implements:

1. Bayesian scoring: `Score(Pi) ∝ P(Pi) × Π P(Ek | Pi)`, normalized over all places
2. Top-5 place selection
3. HMM + Viterbi decoding over the Top-5 to produce a visiting sequence
4. Itinerary output with time slots

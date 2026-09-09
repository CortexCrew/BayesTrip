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

| # | Table | Source | Status |
|---|-------|--------|--------|
| 1 | 01_Place_Master | Fixed list of 20 Chennai places | done |
| 2 | 07_Coordinates | OSM Nominatim geocoding | done |
| 3 | 02_BN_Prior | OpenTripMap `rate` (POI popularity) | implemented, pending `OPENTRIPMAP_API_KEY` |
| 4 | 03_BN_CPT | Web research + structured extraction, deterministic normalization | done |
| 5 | 04_HMM_Initial | OSRM travel time from Chennai Central | done |
| 6 | 05_HMM_Transition | OSRM pairwise travel time, 20x20 | done |
| 7 | 06_HMM_Emission | Researched opening hours, deterministic slot scoring | done |
| 8 | 08_Evidence | Provenance log for every fact used above | done (re-run once 02_BN_Prior lands) |
| 9 | 09_Validation | Automated PASS/FAIL checks on all normalizations | done (5/6 pass; 02_BN_Prior pending) |

See [DESIGN.md](DESIGN.md) for exact formulas and data source details.

## Recommendation engine

`recommendation_engine/` implements:

1. Bayesian scoring: `Score(Pi) ∝ P(Pi) × Π P(Ek | Pi)`, normalized over all places
2. Top-5 place selection
3. HMM + Viterbi decoding over the Top-5 to produce a visiting sequence
4. Itinerary output with time slots

## Setup

```
python -m venv .venv
.venv\Scripts\activate        # or source .venv/bin/activate on Linux/macOS
pip install -r requirements-dev.txt
```

## Running the pipeline

Each step is its own module, run in order (each writes/updates its sheet in
`data/BayesTrip_Data.xlsx`):

```
python -m data_generation.step01_place_master
python -m data_generation.step02_coordinates
python -m data_generation.step03_bn_prior      # needs OPENTRIPMAP_API_KEY
python -m data_generation.step04_bn_cpt
python -m data_generation.step05_hmm_initial
python -m data_generation.step06_hmm_transition
python -m data_generation.step07_hmm_emission
python -m data_generation.step08_evidence      # re-run last, after all others
python -m data_generation.step09_validation
```

Try the recommendation engine end to end (requires 02_BN_Prior to exist):

```
python -m recommendation_engine.pipeline
```

## Tests

```
python -m pytest tests/
```

Covers the pieces that need no network access or API key: CPT and emission
normalization, Bayesian posterior scoring, and Viterbi decoding.

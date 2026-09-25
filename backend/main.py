"""FastAPI backend for BayesTrip — wraps the recommendation engine as a REST API."""

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to sys.path so recommendation_engine imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from recommendation_engine.bayesian_inference import Evidence
from recommendation_engine.pipeline import recommend
from recommendation_engine.cli import OPTIONS
from data_generation.common.places import PLACES
from data_generation.common.workbook import read_sheet


class RecommendRequest(BaseModel):
    age: str
    budget: str
    interest: str
    travel_type: str
    weather: str


app = FastAPI(title="BayesTrip API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/options")
def get_options():
    """Return evidence variable choices for the recommender form."""
    return OPTIONS


@app.get("/api/places")
def get_places():
    """Return all 20 destinations with coordinates."""
    try:
        coords = read_sheet("07_Coordinates")
        coords_dict = coords.set_index("place_id").to_dict("index")
    except Exception:
        coords_dict = {}

    places = []
    for p in PLACES:
        place_data = {
            "place_id": p["place_id"],
            "name": p["name"],
            "category": p["category"],
        }
        if p["place_id"] in coords_dict:
            c = coords_dict[p["place_id"]]
            place_data["lat"] = float(c.get("latitude", 0))
            place_data["lng"] = float(c.get("longitude", 0))
        places.append(place_data)
    return places


@app.post("/api/recommend")
def recommend_endpoint(req: RecommendRequest):
    """Run the full pipeline: Bayesian posterior → Top-5 → HMM/Viterbi → itinerary."""
    try:
        evidence = Evidence(
            age=req.age,
            budget=req.budget,
            interest=req.interest,
            travel_type=req.travel_type,
            weather=req.weather,
        )
        stops, ranked = recommend(evidence)
        return {
            "top5": ranked,
            "itinerary": [
                {
                    "slot": s.slot,
                    "time_range": s.time_range,
                    "place_id": s.place_id,
                    "name": s.name,
                    "lat": s.lat,
                    "lng": s.lng,
                }
                for s in stops
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation engine error: {str(e)}")

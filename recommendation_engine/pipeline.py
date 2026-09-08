"""End-to-end recommendation pipeline: evidence -> Bayesian posterior -> Top-5 ->
HMM/Viterbi -> timed itinerary. Ties together bayesian_inference, hmm_viterbi and
itinerary; each of those stays independently usable and testable."""

from recommendation_engine.bayesian_inference import Evidence, top_n
from recommendation_engine.hmm_viterbi import decode_sequence
from recommendation_engine.itinerary import ItineraryStop, build_itinerary


def recommend(evidence: Evidence) -> tuple[list[ItineraryStop], list[dict]]:
    """Returns (itinerary_stops, top5_ranked) where top5_ranked is the Bayesian
    Top-5 (place_id, name, posterior) for transparency/debugging."""
    top5 = top_n(evidence, n=5)
    place_ids = top5["place_id"].tolist()

    sequence = decode_sequence(place_ids)
    stops = build_itinerary(sequence)

    return stops, top5.to_dict("records")


if __name__ == "__main__":
    from recommendation_engine.itinerary import print_itinerary

    example = Evidence(age="Student", budget="Low", interest="History", travel_type="Friends", weather="Sunny")
    stops, ranked = recommend(example)

    print("Top-5 by posterior:")
    for r in ranked:
        print(f"  {r['place_id']} {r['name']}: {r['posterior']:.4f}")

    print("\nItinerary:")
    print_itinerary(stops)

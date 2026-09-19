
from recommendation_engine.bayesian_inference import Evidence
from recommendation_engine.itinerary import print_itinerary
from recommendation_engine.pipeline import recommend

OPTIONS = {
    "age": ["Student", "Adult"],
    "budget": ["Low", "Medium", "High"],
    "interest": ["History", "Nature", "Spiritual", "Shopping", "Entertainment"],
    "travel_type": ["Solo", "Friends", "Family"],
    "weather": ["Sunny", "Rainy"],
}


def _ask(field: str, choices: list[str]) -> str:
    print(f"\n{field.replace('_', ' ').title()}:")
    for i, choice in enumerate(choices, start=1):
        print(f"  {i}. {choice}")
    while True:
        raw = input(f"Choose 1-{len(choices)}: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        print("Invalid choice, try again.")


def main() -> None:
    print("=== BayesTrip: tell us about your trip ===")
    answers = {field: _ask(field, choices) for field, choices in OPTIONS.items()}
    evidence = Evidence(**answers)

    stops, ranked = recommend(evidence)

    print("\nTop-5 destinations (Bayesian posterior):")
    for r in ranked:
        print(f"  {r['place_id']} {r['name']}: {r['posterior']:.4f}")

    print("\nItinerary (HMM-decoded visiting order):")
    print_itinerary(stops)


if __name__ == "__main__":
    main()

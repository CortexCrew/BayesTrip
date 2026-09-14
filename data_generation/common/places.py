"""The fixed list of 20 Chennai destinations used across every table in the pipeline."""

PLACES = [
    {"place_id": "P01", "name": "Marina Beach", "category": "Nature / Recreation"},
    {"place_id": "P02", "name": "Fort St. George", "category": "History & Heritage"},
    {"place_id": "P03", "name": "Kapaleeshwarar Temple", "category": "Spiritual / Heritage"},
    {
        "place_id": "P04",
        "name": "San Thome Basilica",
        "category": "Spiritual / Heritage",
        # "Santhome Cathedral, ..." (used for the earlier Nominatim step) resolves to
        # the wrong POI (a school) under Geoapify; "St Thomas Basilica" is the query
        # Geoapify matches correctly to the actual basilica.
        "geocode_query": "St Thomas Basilica, Chennai, India",
    },
    {"place_id": "P05", "name": "Government Museum, Chennai", "category": "History & Heritage"},
    {"place_id": "P06", "name": "Guindy National Park", "category": "Nature"},
    {
        "place_id": "P07",
        "name": "Arignar Anna Zoological Park (Vandalur Zoo)",
        "category": "Nature / Family",
        # The parenthetical alt-name in the canonical name breaks Geoapify's parser
        # (falls back to a city-level match); the plain name without parens resolves
        # correctly to the actual zoo.
        "geocode_query": "Arignar Anna Zoological Park, Vandalur, Chennai, Tamil Nadu, India",
    },
    {"place_id": "P08", "name": "Valluvar Kottam", "category": "History & Heritage"},
    {"place_id": "P09", "name": "Birla Planetarium", "category": "Science / Entertainment"},
    {"place_id": "P10", "name": "Semmozhi Poonga", "category": "Nature"},
    {"place_id": "P11", "name": "Elliot's Beach", "category": "Nature / Recreation"},
    {"place_id": "P12", "name": "Besant Nagar Beach", "category": "Nature / Recreation"},
    {
        "place_id": "P13",
        "name": "DakshinaChitra",
        "category": "Culture / Heritage",
        # Geoapify's OSM-sourced data spells this "Dakshin Chitra" (missing the 'a'
        # before Chitra) rather than the canonical "DakshinaChitra" -- close enough to
        # pass the fuzzy category-word check in step02_coordinates.py.
        "geocode_query": "Dakshin Chitra, Muttukadu, Tamil Nadu, India",
    },
    {"place_id": "P14", "name": "Cholamandal Artists' Village", "category": "Art / Culture"},
    {
        "place_id": "P15",
        "name": "Vivekananda House",
        "category": "History / Heritage",
        # "Vivekanandar Illam" (its Tamil name, used for the earlier Nominatim step)
        # returns no results under Geoapify. "Ice House" -- its historical name, from
        # when the building stored ice imported from the US in the 1840s -- resolves
        # correctly to the same building.
        "geocode_query": ["Vivekanandar Illam, Chennai, India", "Ice House, Chennai, Tamil Nadu, India"],
    },
    {"place_id": "P16", "name": "Thousand Lights Mosque", "category": "Spiritual / Heritage"},
    {"place_id": "P17", "name": "Parthasarathy Temple", "category": "Spiritual / Heritage"},
    {"place_id": "P18", "name": "Vadapalani Murugan Temple", "category": "Spiritual"},
    {"place_id": "P19", "name": "Express Avenue", "category": "Shopping / Entertainment"},
    {"place_id": "P20", "name": "MGM Dizzee World", "category": "Entertainment / Family"},
]

CITY = "Chennai"
STATUS_ACTIVE = "active"

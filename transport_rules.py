# transport_rules.py — India-only transport validation
from transport_ml import transport_ml  # type: ignore

# ─────────────────────────────────────────────────────
# Known Indian city pairs with approximate distances (km)
# ─────────────────────────────────────────────────────
INDIA_DISTANCES = {
    # North India
    ("delhi", "jaipur"): 280,
    ("delhi", "agra"): 200,
    ("delhi", "chandigarh"): 250,
    ("delhi", "shimla"): 340,
    ("delhi", "haridwar"): 210,
    ("delhi", "amritsar"): 450,
    ("delhi", "lucknow"): 550,
    ("delhi", "varanasi"): 820,
    ("delhi", "patna"): 1000,
    ("delhi", "kolkata"): 1500,
    ("delhi", "mumbai"): 1400,
    ("delhi", "goa"): 1900,
    ("delhi", "bangalore"): 2150,
    ("delhi", "chennai"): 2180,
    ("delhi", "hyderabad"): 1580,
    ("delhi", "ahmedabad"): 950,
    ("delhi", "manali"): 570,
    # East India
    ("kolkata", "bhubaneswar"): 440,
    ("kolkata", "patna"): 590,
    ("kolkata", "guwahati"): 1030,
    ("kolkata", "darjeeling"): 640,
    ("kolkata", "puri"): 500,
    ("kolkata", "varanasi"): 680,
    # West India
    ("mumbai", "goa"): 590,
    ("mumbai", "pune"): 150,
    ("mumbai", "nashik"): 170,
    ("mumbai", "ahmedabad"): 530,
    ("mumbai", "bangalore"): 980,
    ("mumbai", "hyderabad"): 710,
    ("mumbai", "kolkata"): 2050,
    ("mumbai", "chennai"): 1330,
    # South India
    ("bangalore", "mysuru"): 150,
    ("bangalore", "mysore"): 150,
    ("bangalore", "coorg"): 250,
    ("bangalore", "ooty"): 310,
    ("bangalore", "chennai"): 350,
    ("bangalore", "hyderabad"): 570,
    ("bangalore", "kochi"): 540,
    ("bangalore", "goa"): 570,
    ("chennai", "pondicherry"): 160,
    ("chennai", "madurai"): 460,
    ("chennai", "coimbatore"): 490,
    ("chennai", "kochi"): 680,
    ("hyderabad", "warangal"): 150,
    ("hyderabad", "vijayawada"): 270,
    # North-East
    ("guwahati", "shillong"): 100,
    ("guwahati", "dibrugarh"): 470,
}

# Build reverse mapping too
_DISTANCES = {}
for (a, b), d in INDIA_DISTANCES.items():
    _DISTANCES[(a, b)] = d
    _DISTANCES[(b, a)] = d

# All supported Indian cities
INDIA_CITIES = sorted(set(c for pair in INDIA_DISTANCES.keys() for c in pair))

def estimate_distance(origin: str, destination: str) -> int:
    key = (origin.lower().strip(), destination.lower().strip())
    return _DISTANCES.get(key, 800)  # default 800 km if unknown pair

def get_allowed_modes(origin: str, destination: str, budget_per_person: int = 5000, travel_days: int = 3) -> list:
    """
    Returns allowed transport modes using an ML (RandomForest) prediction model.
    It takes distance, budget per person, and travel days into account.
    If distance < 300km, flight options are strictly removed.
    """
    dist = estimate_distance(origin, destination)
    return transport_ml.predict_modes(dist, budget_per_person, travel_days)

def is_known_city(city: str) -> bool:
    return city.lower().strip() in INDIA_CITIES

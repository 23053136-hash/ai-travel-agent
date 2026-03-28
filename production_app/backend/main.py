import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import SearchRequest, TravelPlanResponse
from services.gemini import parse_user_input
from engine import haversine, generate_transport_options, suggest_hotels
from data import CITIES

app = FastAPI(title="AI Travel Engine Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def find_city_match(city_raw: str):
    cl = city_raw.lower()
    for cname, cdata in CITIES.items():
        if cname in cl or cl in cname:
            return cname, cdata
    # Fallback to nearest substring match or return None
    return None, None

@app.post("/plan", response_model=TravelPlanResponse)
async def plan_trip(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. AI Parsing
    parsed = parse_user_input(req.query)
    
    o_name = parsed.get("origin", "")
    d_name = parsed.get("destination", "")
    budget = float(parsed.get("budget", 15000))
    
    if not o_name or not d_name:
        return TravelPlanResponse(
            origin=o_name, destination=d_name, distance_km=0, budget=budget,
            transport_options=[], hotels=[],
            error="Could not detect origin and destination from query."
        )

    # 2. Distance Computation
    o_match, o_data = find_city_match(o_name)
    d_match, d_data = find_city_match(d_name)

    if not o_match or not d_match:
        return TravelPlanResponse(
            origin=o_name, destination=d_name, distance_km=0, budget=budget,
            transport_options=[], hotels=[],
            error=f"City unrecognized. Currently supported dataset: {', '.join(CITIES.keys()).title()}"
        )

    lat1, lon1 = o_data["lat"], o_data["lon"]
    lat2, lon2 = d_data["lat"], d_data["lon"]
    
    dist_km = haversine(lat1, lon1, lat2, lon2)
    
    # 3. Transport Engine Rules
    transport_opts = generate_transport_options(o_match, d_match, dist_km)

    # 4. Hotel Engine Rules
    hotels = suggest_hotels(budget)
    
    return TravelPlanResponse(
        origin=o_match.title(),
        destination=d_match.title(),
        distance_km=round(dist_km, 1),
        budget=budget,
        transport_options=transport_opts,
        hotels=hotels
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

import math
import random
from data import CITIES
from models import TransportOption, HotelOption

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def estimate_cost(mode: str, distance_km: float) -> float:
    if mode == "flight":
        base = 1500 + (distance_km * 5.0)
    elif mode == "train_sleeper":
        base = distance_km * 0.45
    elif mode == "train_3ac":
        base = distance_km * 1.10
    elif mode == "train_2ac":
        base = distance_km * 1.60
    elif mode == "train_1ac":
        base = distance_km * 2.80
    elif mode == "bus":
        base = distance_km * 0.5
    else:
        base = 0.0
    
    variation = random.uniform(0.9, 1.1)
    return round(float(base * variation), 2) # type: ignore

def estimate_time(mode: str, distance_km: float) -> float:
    # Flight speed: ~600 km/h, Train speed: ~60 km/h, Bus speed: ~40 km/h
    if mode == "flight":
        return round(float(distance_km / 600.0 + 1.5), 1) # Including airport overhead # type: ignore
    elif "train" in mode:
        speed = 55.0 if "sleeper" in mode else 65.0
        return round(float(distance_km / speed), 1) # type: ignore
    elif mode == "bus":
        return round(float(distance_km / 40.0), 1) # type: ignore
    return 0.0

def generate_transport_options(origin: str, destination: str, distance_km: float):
    # Validation Rules
    allowed_modes = []
    
    is_international = False
    
    if is_international:
        allowed_modes = ["flight"]
    else:
        if distance_km < 300:
            allowed_modes = ["bus", "train"]
        elif 300 <= distance_km <= 800:
            allowed_modes = ["train", "flight"]
        else:
            allowed_modes = ["flight", "train"]
            
    # Do NOT allow bus for very long distances (>1000 km)
    if distance_km > 1000 and "bus" in allowed_modes:
        allowed_modes.remove("bus")

    options = []
    for mode in allowed_modes:
        if mode == "train":
            # Expand into specific Indian tiers
            for tier in ["train_sleeper", "train_3ac", "train_2ac", "train_1ac"]:
                # Only offer 1AC for longer distances or high budgets
                if tier == "train_1ac" and distance_km < 500: continue
                
                cost = estimate_cost(tier, distance_km)
                time_h = estimate_time(tier, distance_km)
                options.append({
                    "mode": tier.replace("_", " ").title(),
                    "price": cost,
                    "time_hours": time_h
                })
        else:
            cost = estimate_cost(mode, distance_km)
            time_h = estimate_time(mode, distance_km)
            options.append({
                "mode": mode.title(),
                "price": cost,
                "time_hours": time_h
            })

    if not options:
        return []

    # Scoring System
    max_price = max(o["price"] for o in options)
    min_price = min(o["price"] for o in options)
    
    max_time = max(o["time_hours"] for o in options)
    min_time = min(o["time_hours"] for o in options)

    for o in options:
        # Cost score: 100 = cheapest
        if max_price == min_price:
            cost_score = 100.0
        else:
            cost_score = 100.0 * (1.0 - ((float(o["price"]) - float(min_price)) / (float(max_price) - float(min_price)))) # type: ignore
            
        # Time score: 100 = fastest
        if max_time == min_time:
            time_score = 100.0
        else:
            time_score = 100.0 * (1.0 - ((float(o["time_hours"]) - float(min_time)) / (float(max_time) - float(min_time)))) # type: ignore

        o["cost_score"] = round(cost_score, 1) # type: ignore
        o["time_score"] = round(time_score, 1) # type: ignore
        o["final_score"] = round((cost_score + time_score) / 2.0, 1) # type: ignore

    # Convert to objects
    transport_objs = []
    for o in options:
        transport_objs.append(TransportOption(**o, label=""))
        
    # Assign labels
    cheapest = min(transport_objs, key=lambda x: x.price)
    fastest = min(transport_objs, key=lambda x: x.time_hours)
    best = max(transport_objs, key=lambda x: x.final_score)
    
    for obj in transport_objs:
        labels = []
        if obj.mode == cheapest.mode: labels.append("Cheapest Plan 💰")
        if obj.mode == fastest.mode: labels.append("Fastest Plan ⚡")
        if obj.mode == best.mode: labels.append("Best Balanced Plan ⭐")
        obj.label = " | ".join(labels) if labels else "Standard Option"

    return transport_objs

def suggest_hotels(budget: float) -> list[HotelOption]:
    # Hardcoded realistic mock data per requirements
    per_night = budget / 3 
    
    if per_night < 2000:
        return [
            HotelOption(name="Zostel Backpacker", price_per_night=800, category="Hostel / Dorms"),
            HotelOption(name="City Budget Stay", price_per_night=1500, category="Budget Server")
        ]
    elif per_night < 5000:
        return [
            HotelOption(name="Comfort Inn", price_per_night=3000, category="Comfort 3-Star"),
            HotelOption(name="Radisson Blu", price_per_night=4500, category="Premium 4-Star")
        ]
    else:
        return [
            HotelOption(name="Taj Mahal Palace", price_per_night=15000, category="Luxury 5-Star"),
            HotelOption(name="The Oberoi Grand", price_per_night=12000, category="Premium 4-Star")
        ]

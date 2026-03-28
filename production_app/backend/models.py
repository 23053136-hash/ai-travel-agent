from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str

class TransportOption(BaseModel):
    mode: str
    price: float
    time_hours: float
    cost_score: float
    time_score: float
    final_score: float
    label: str

class HotelOption(BaseModel):
    name: str
    price_per_night: float
    category: str

class TravelPlanResponse(BaseModel):
    origin: str
    destination: str
    distance_km: float
    budget: float
    transport_options: List[TransportOption]
    hotels: List[HotelOption]
    error: Optional[str] = None

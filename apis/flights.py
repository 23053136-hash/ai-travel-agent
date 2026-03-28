# apis/flights.py
# Kiwi.com Tequila API — 100% FREE (1000 calls/month, no credit card)
# Sign up: https://tequila.kiwi.com → Register → Copy API Key

from __future__ import annotations

import os
from typing import Any
import requests  # type: ignore[import-untyped]
from dotenv import load_dotenv  # type: ignore[import-untyped]

load_dotenv()

KIWI_SEARCH_URL = "https://api.tequila.kiwi.com/v2/search"


def search_flights(
    origin_iata: str,
    dest_iata: str,
    date: str,  # YYYY-MM-DD
    adults: int = 1,
) -> list[dict[str, object]]:
    """
    Search real domestic flights using Kiwi.com Tequila API (FREE).
    Returns top 3 cheapest options, or empty list if API key not set.
    """
    api_key: str = os.getenv("KIWI_API_KEY", "")
    if not api_key or "your_" in api_key:
        return []  # No key — caller uses smart estimated links

    # Format date: YYYY-MM-DD → DD/MM/YYYY
    try:
        parts = date.split("-")
        kiwi_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        return []

    try:
        r = requests.get(
            KIWI_SEARCH_URL,
            headers={"apikey": api_key},
            params={
                "fly_from": origin_iata,
                "fly_to": dest_iata,
                "date_from": kiwi_date,
                "date_to": kiwi_date,
                "adults": adults,
                "curr": "INR",
                "limit": 3,
                "sort": "price",
                "max_stopovers": 1,
                "partner_market": "in",
            },
            timeout=15,
        )
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        offers: list[dict[str, Any]] = data.get("data", [])

        results: list[dict[str, object]] = []
        for offer in offers:
            price: int = int(offer.get("price", 0))
            airline: str = str(offer.get("airlines", ["??"])[0])
            duration_sec: int = int(offer.get("duration", {}).get("total", 0))
            hours: int = duration_sec // 3600
            mins: int = (duration_sec % 3600) // 60
            stops: int = len(offer.get("route", [])) - 1
            results.append({
                "airline": airline,
                "price": price,
                "duration": f"{hours}h {mins}m",
                "stops": max(0, stops),
            })
        return results

    except Exception as e:
        print(f"[Kiwi flights error]: {e}")
        return []

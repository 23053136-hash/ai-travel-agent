# agents.py — India-only Multi-Agent Travel System
# Uses: Gemini (free) + Amadeus sandbox (free) + smart URL construction

from __future__ import annotations

import os
import json
import re
import math
from typing import Any, Optional
from dotenv import load_dotenv  # type: ignore[import-untyped]
from transport_rules import get_allowed_modes, estimate_distance, is_known_city, INDIA_CITIES

load_dotenv()

# ─────────────────────────────────────────────
# Gemini Setup
# ─────────────────────────────────────────────
GEMINI_KEY: str = os.getenv("GEMINI_API_KEY", "")
gemini_available: bool = False
model: Optional[Any] = None

if GEMINI_KEY and "your_" not in GEMINI_KEY:
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=GEMINI_KEY)  # type: ignore
        model = genai.GenerativeModel("gemini-1.5-flash")  # type: ignore
        gemini_available = True
        print("[Gemini] Connected ✅")
    except Exception as e:
        print(f"[Gemini Init Error]: {e}")

def call_gemini(prompt: str) -> str:
    """Call Gemini Flash and return text or empty string on failure."""
    if not gemini_available or model is None:
        return ""
    try:
        active_model: Any = model  # narrow type for Pyre2
        resp = active_model.generate_content(prompt)  # type: ignore[union-attr]
        text: Optional[str] = getattr(resp, "text", None)
        return text.strip() if text else ""
    except Exception as e:
        print(f"[Gemini Error]: {e}")
        return ""

# ─────────────────────────────────────────────
# India-only IATA Codes
# ─────────────────────────────────────────────
IATA_CODES = {
    "delhi": "DEL", "new delhi": "DEL",
    "mumbai": "BOM", "bombay": "BOM",
    "goa": "GOI",
    "bangalore": "BLR", "bengaluru": "BLR",
    "kolkata": "CCU", "calcutta": "CCU",
    "chennai": "MAA", "madras": "MAA",
    "hyderabad": "HYD",
    "ahmedabad": "AMD",
    "jaipur": "JAI",
    "kochi": "COK",
    "pune": "PNQ",
    "bhubaneswar": "BBI",
    "lucknow": "LKO",
    "patna": "PAT",
    "varanasi": "VNS",
    "agra": "AGR",
    "amritsar": "ATQ",
    "shimla": "SLV",
    "manali": "KUU",
    "chandigarh": "IXC",
    "haridwar": "DEL",   # nearest airport is Delhi
    "darjeeling": "IXB",
    "guwahati": "GAU",
    "madurai": "IXM",
    "coimbatore": "CJB",
    "visakhapatnam": "VTZ",
    "vijayawada": "VGA",
    "puri": "BBI",       # nearest = bhubaneswar
    "nashik": "BOM",     # nearest = mumbai
    "mysuru": "MYQ", "mysore": "MYQ",
    "pondicherry": "MAA", # nearest = chennai
    "ooty": "CJB",       # nearest = coimbatore
    "coorg": "MYQ",      # nearest = mysore
    "shillong": "GAU",
    "dibrugarh": "DIB",
    "warangal": "HYD",
    "phuket": "HKT",
}

# IRCTC station codes for smart train links
STATION_CODES = {
    "delhi": "NDLS", "new delhi": "NDLS",
    "mumbai": "CSTM", "bombay": "CSTM",
    "goa": "MAO",
    "bangalore": "SBC", "bengaluru": "SBC",
    "kolkata": "HWH", "calcutta": "HWH",
    "chennai": "MAS", "madras": "MAS",
    "hyderabad": "SC",
    "ahmedabad": "ADI",
    "jaipur": "JP",
    "kochi": "ERS",
    "pune": "PUNE",
    "bhubaneswar": "BBS",
    "lucknow": "LKO",
    "patna": "PNBE",
    "varanasi": "BSB",
    "agra": "AF",
    "amritsar": "ASR",
    "chandigarh": "CDG",
    "haridwar": "HW",
    "darjeeling": "NJP",
    "guwahati": "GHY",
    "madurai": "MDU",
    "coimbatore": "CBE",
    "visakhapatnam": "VSKP",
    "vijayawada": "BZA",
    "puri": "PURI",
    "mysuru": "MYS", "mysore": "MYS",
    "manali": "PTKT",
    "nashik": "NK",
    "shimla": "SML",
}

# MakeMyTrip hotel city codes (used in hotel-listing URLs)
MMT_HOTEL_CITY_CODES: dict[str, str] = {
    "delhi": "CTDEL",     "new delhi": "CTDEL",
    "mumbai": "CTBOM",    "bombay": "CTBOM",
    "goa": "CTGOI",
    "bangalore": "CTBLR", "bengaluru": "CTBLR",
    "kolkata": "CTCCU",   "calcutta": "CTCCU",
    "chennai": "CTMAA",   "madras": "CTMAA",
    "hyderabad": "CTHYD",
    "ahmedabad": "CTAMD",
    "jaipur": "CTJAI",
    "kochi": "CTCOK",
    "pune": "CTPNQ",
    "varanasi": "CTVNS",
    "lucknow": "CTLKO",
    "amritsar": "CTATQ",
    "agra": "CTAGR",
    "shimla": "CTSLV",
    "manali": "CTKUU",
    "darjeeling": "CTIXB",
    "guwahati": "CTGAU",
    "mysuru": "CTMYQ",  "mysore": "CTMYQ",
    "ooty": "CTOOTY",
    "coorg": "CTCORG",
}

def get_mmt_city(city: str) -> str:
    result: Optional[str] = MMT_HOTEL_CITY_CODES.get(city.lower().strip())
    return result if result else (city.upper() + "XXX")[0:3]  # type: ignore[index]

def date_parts(date_str: str) -> dict[str, str]:
    """Parse YYYY-MM-DD into all needed formats for booking links."""
    try:
        chars = list(date_str)
        dd   = "".join(chars[8:10])   # type: ignore[index]  # Pyre2 slice bug
        mm   = "".join(chars[5:7])    # type: ignore[index]
        yyyy = "".join(chars[0:4])    # type: ignore[index]
    except IndexError:
        dd, mm, yyyy = "01", "01", "2026"
    return {
        "dd": dd, "mm": mm, "yyyy": yyyy,
        # MakeMyTrip flight format (from browser inspection): DD/MM/YYYY in itinerary param
        "mmt_flight": f"{dd}/{mm}/{yyyy}",        # 20/04/2026
        # MakeMyTrip hotel: MMDDYYYY
        "mmt_hotel":  f"{mm}{dd}{yyyy}",          # 04202026
        # IRCTC: YYYYMMDD
        "irctc":      f"{yyyy}{mm}{dd}",          # 20260420
        # redBus / Cleartrip display: DD-MM-YYYY
        "redbus":     f"{dd}-{mm}-{yyyy}",        # 20-04-2026
        # Ixigo: DD-MMM-YYYY (e.g. 20-Apr-2026)
        "ixigo":      f"{dd}-{_month_abbr(mm)}-{yyyy}",
    }

_MONTH_ABBRS = ["","Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]
def _month_abbr(mm: str) -> str:
    try:
        return _MONTH_ABBRS[int(mm)]
    except Exception:
        return mm

def get_iata(city: str) -> str:
    result = IATA_CODES.get(str(city).lower().strip())
    if result is not None:
        return str(result)
    # Use explicit casting to satisfy strict type checkers
    f_val: str = str(city).upper()
    return f_val[0:3] # type: ignore
 
def get_station(city: str) -> str:
    result = STATION_CODES.get(str(city).lower().strip())
    if result is not None:
        return str(result)
    # Use explicit casting to satisfy strict type checkers
    f_val: str = str(city).upper()
    return f_val[0:3] # type: ignore

WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

def blank_memory():
    return {
        "destination": "",
        "origin": "",
        "dest_iata": "",
        "origin_iata": "",
        "origin_station": "",
        "dest_station": "",
        "date": "",
        "budget": "",
        "travelers": "",
        "days": "",
        "trip_type": "",
        "preferences": [],
        "_pending_field": ""
    }

# ─────────────────────────────────────────────
# Agent 1: Memory Agent
# ─────────────────────────────────────────────
class MemoryAgent:
    def process(self, text: str, memory: dict, pending_field: str = "") -> dict:
        if gemini_available:
            memory = self._extract_with_gemini(text, memory)
        else:
            memory = self._extract_with_rules(text, memory, pending_field)

        # Enrich codes
        if memory["origin"]:
            memory["origin_iata"] = get_iata(memory["origin"])
            memory["origin_station"] = get_station(memory["origin"])
        if memory["destination"]:
            memory["dest_iata"] = get_iata(memory["destination"])
            memory["dest_station"] = get_station(memory["destination"])

        return memory

    def _extract_with_gemini(self, text: str, memory: dict) -> dict:
        city_list = ", ".join(sorted(set(INDIA_CITIES)))
        prompt = f"""
You are a travel data extraction agent for an India-only travel app.
Current memory: {json.dumps(memory)}
User message: "{text}"

Only extract data for Indian cities. Supported cities: {city_list}

Rules:
- Never overwrite a non-empty field unless user explicitly corrects it
- budget: "20k"=20000, "50,000"=50000, "₹15000"=15000
- travelers: "me and 2 friends"=3, "alone"=1, "family of 4"=4
- days: "3 days"=3, "a week"=7, "weekend"=2
- date format: YYYY-MM-DD. If user says "April 20" use 2026-04-20
- trip_type: beach, adventure, cultural, romantic, family, pilgrimage, hill station, etc.
- If city is not in supported list, leave the field empty

Return ONLY valid JSON:
{{
  "destination": "",
  "origin": "",
  "date": "",
  "budget": "",
  "travelers": "",
  "days": "",
  "trip_type": "",
  "preferences": []
}}
"""
        raw = call_gemini(prompt)
        raw = re.sub(r"```json|```", "", raw).strip()
        try:
            extracted = json.loads(raw)
            for key in ["destination", "origin", "date", "budget", "travelers", "days", "trip_type"]:
                val = str(extracted.get(key, "")).strip()
                if val and val.lower() != "null" and val != "":
                    # Validate cities against known list
                    if key in ("destination", "origin"):
                        if not is_known_city(val):
                            continue
                    memory[key] = val
            prefs = extracted.get("preferences", [])
            if isinstance(prefs, list):
                memory["preferences"] = list(set(memory.get("preferences", []) + prefs))
        except Exception as e:
            raw_preview = str(raw)[:200] if raw else "None" # type: ignore
            print(f"[MemoryAgent parse error]: {e} | raw: {raw_preview}")
        return memory

    def _extract_with_rules(self, text: str, memory: dict, pending_field: str = "") -> dict:
        t = text.lower().strip()

        # DATE first (so 2026 from date won't pollute budget)
        if not memory["date"]:
            dm = re.search(r'(\d{4}-\d{2}-\d{2})', text)
            if dm:
                memory["date"] = dm.group(1)

        # CITIES — handle "X to Y" pattern
        if not memory["destination"] or not memory["origin"]:
            to_m = re.search(r'(?:from\s+)?([a-z]+(?:\s+[a-z]+)?)\s+to\s+([a-z]+(?:\s+[a-z]+)?)', t)
            if to_m:
                c1, c2 = to_m.group(1).strip(), to_m.group(2).strip()
                for city in INDIA_CITIES:
                    if city == c1 and not memory["origin"] and is_known_city(c1):
                        memory["origin"] = city.title()
                    if city == c2 and not memory["destination"] and is_known_city(c2):
                        memory["destination"] = city.title()
            else:
                # Single city — use pending context
                target = pending_field if pending_field in ("destination", "origin") else "destination"
                for city in INDIA_CITIES:
                    if city in t and is_known_city(city):
                        if target == "destination" and not memory["destination"]:
                            memory["destination"] = city.title()
                        elif target == "origin" and not memory["origin"]:
                            memory["origin"] = city.title()
                        break

        # TRAVELERS — word numbers + contextual standalone digits
        if not memory["travelers"]:
            if any(w in t for w in ("alone", "solo", "myself", "just me")):
                memory["travelers"] = "1"
            else:
                for word, num in WORD_TO_NUM.items():
                    if re.search(rf'\b{word}\b', t):
                        memory["travelers"] = str(num)
                        break
                if not memory["travelers"]:
                    m = re.search(r'(\d+)\s*(person|people|traveler|passenger|adult|pax)', t)
                    if m:
                        memory["travelers"] = m.group(1)
                    elif pending_field == "travelers":
                        m2 = re.search(r'\b([1-9]|1[0-9]|20)\b', t)
                        if m2:
                            memory["travelers"] = m2.group(1)

        # DAYS
        if not memory["days"]:
            mdays = re.search(r'(\d+)\s*(days?|nights?|week|month)', t)
            if mdays:
                val = int(mdays.group(1))
                if 'week' in mdays.group(2): val *= 7
                if 'month' in mdays.group(2): val *= 30
                memory["days"] = str(val)
            elif pending_field == "days":
                m2 = re.search(r'\b(\d+)\b', t)
                if m2:
                    val = int(m2.group(1))
                    if val < 365:
                        memory["days"] = str(val)

        # BUDGET — skip years (1800-2100) and dates
        if not memory["budget"]:
            km = re.search(r'(\d+)\s*k\b', t)
            if km:
                memory["budget"] = str(int(km.group(1)) * 1000)
            elif pending_field == "budget" or any(w in t for w in ("rs", "rupee", "inr", "₹", "budget", "spend")):
                for n in re.findall(r'\b\d[\d,]*\b', text):
                    val = int(n.replace(",", ""))
                    if 1800 <= val <= 2100:
                        continue
                    if val < 500:
                        continue
                    memory["budget"] = str(val)
                    break

        return memory


# ─────────────────────────────────────────────
# Agent 2: Conversation Agent
# ─────────────────────────────────────────────
class ConversationAgent:
    REQUIRED = ["destination", "origin", "date", "budget", "travelers", "days"]

    def get_missing(self, memory: dict) -> list:
        return [f for f in self.REQUIRED if not memory.get(f)]

    def get_next_question(self, memory: dict, last_input: str) -> dict:
        missing = self.get_missing(memory)
        if not missing:
            return {"status": "complete", "message": "Perfect 👍 I have everything I need. Planning your trip now..."}

        if gemini_available:
            return self._ask_with_gemini(memory, missing)
        return self._ask_with_rules(memory, missing)

    def _ask_with_gemini(self, memory: dict, missing: list) -> dict:  # type: ignore[type-arg]
        cities_all: list[str] = list(sorted(set(INDIA_CITIES)))
        cities_short: list[str] = []
        for i, c in enumerate(cities_all):
            if i >= 30:
                break
            cities_short.append(c)
        cities_str = ", ".join(cities_short) + "... and more"
        prompt = f"""
You are an Elite AI Travel Concierge for India-only travel.
Trip memory so far: {json.dumps(memory)}
Missing fields: {missing}

Ask for ONLY the first missing field. Be warm, friendly, concise — like a premium human agent.
If asking for destination/origin, mention a few example cities: {cities_str}
If asking for date: suggest format like "2026-04-20"
If asking for budget: give ₹ examples
Return plain text only. No JSON. Max 2 sentences.
"""
        msg = call_gemini(prompt)
        if not msg:
            msg = self._ask_with_rules(memory, missing)["message"]
        return {"status": "incomplete", "message": msg}

    def _ask_with_rules(self, memory: dict, missing: list) -> dict:
        field = missing[0]
        dest = memory.get("destination", "your destination")
        origin = memory.get("origin", "your city")
        msgs = {
            "destination": "Welcome! 👋 Which city in India would you like to visit? (e.g. Goa, Manali, Kerala, Jaipur, Varanasi)",
            "origin": f"Great choice! 😊 {dest} is wonderful. Which city are you traveling from?",
            "date": f"Got it — {origin} to {dest}. What date are you planning your trip? (e.g. 2026-04-20)",
            "budget": "What's your total budget for this trip? (e.g. ₹15,000 or 30k)",
            "travelers": "How many people are traveling?",
            "days": "How many days are you planning to stay? (e.g. 3, 5)",
        }
        return {"status": "incomplete", "message": msgs.get(field, f"Could you share your {field}?")}


# ─────────────────────────────────────────────
# Agent 3: Budget Agent
# ─────────────────────────────────────────────
class BudgetAgent:
    def optimize(self, memory: dict, allowed_modes: list) -> dict:
        raw = str(memory.get("budget", "15000"))
        nums = re.findall(r'\d+', raw.replace(",", ""))
        budget = int(nums[0]) if nums else 15000
        n = max(1, int(memory.get("travelers", "1") or "1"))

        # Adjust split if only train/bus (no flight)
        if "flight" not in allowed_modes:
            transport_pct, hotel_pct, other_pct = 0.25, 0.50, 0.25
        else:
            transport_pct, hotel_pct, other_pct = 0.40, 0.40, 0.20

        transport = math.floor(budget * transport_pct)
        hotel = math.floor(budget * hotel_pct)
        other = math.floor(budget * other_pct)

        # Assume nights = days as per user's specific feedback for this app's logic
        days = max(1, int(str(memory.get("days", "3")) or "3"))
        nights = days
        
        # TRANSPORT: Standard Single-Way Estimation
        transport_total = math.floor(budget * transport_pct)
        
        # Calculate hotel budget as 'nights * per_night_allocation'
        hpn = (budget // n) // (max(1, days + 1)) 
        hotel_total = hpn * n * nights

        # Ensure 'other' (food/misc) is at least 10% of total budget
        min_other = math.floor(budget * 0.10)
        remaining = budget - (int(transport_total) + hotel_total)
        
        deficit_msg = ""
        is_deficit = False
        if remaining < min_other:
            is_deficit = True
            needed = min_other - remaining
            deficit_msg = f"⚠️ Your budget is tight! You may need an additional ₹{needed:,} to comfortably cover all expenses."
            other = min_other
        else:
            other = remaining

        return {
            "total": budget,
            "per_person": budget // n,
            "transport": int(transport_total),
            "hotel": hotel_total,
            "other": other,
            "nights": nights,
            "is_return": False,
            "per_night_info": f"₹{hpn:,} x {nights} nights",
            "warning": "",
            "is_deficit": False,
            "transport_pct": transport_pct,
            "hotel_pct": hotel_pct
        }

    def economic_adjust(self, memory: dict, transport_options: list, hotel_options: list) -> dict:
        """
        Calculates the actual budget based on the MOST ECONOMIC selected paths.
        This overrides the theoretical split with real-world minimal costs.
        """
        n = int(str(memory.get("travelers", "1")) or "1")
        days = max(1, int(str(memory.get("days", "3")) or "3"))
        nights = days
        
        # 1. FIND CHEAPEST TRANSIT
        min_transport_total = 1000000
        for opt in transport_options:
            cost = int(str(opt.get("total_cost", "100000")).replace("₹", "").replace(",", "")) # type: ignore
            if cost < min_transport_total:
                min_transport_total = cost
        
        # 2. FIND CHEAPEST HOTEL
        min_hotel_nightly = 1000000
        for h in hotel_options:
            cost = int(str(h.get("price_per_night", "100000")).replace("₹", "").replace(",", "")) # type: ignore
            if cost < min_hotel_nightly:
                min_hotel_nightly = cost
        
        min_hotel_total = min_hotel_nightly * nights
        
        # 3. CALCULATE OTHER (Food/Misc - min ₹400/person/day)
        min_other_total = n * days * 400
        
        actual_total = min_transport_total + min_hotel_total + min_other_total
        
        return {
            "total": actual_total,
            "per_person": actual_total // n,
            "transport": min_transport_total,
            "hotel": min_hotel_total,
            "other": min_other_total,
            "nights": nights,
            "is_economic": True
        }

    def calculate_tiers(self, memory: dict, distance_km: int) -> dict:
        """Calculates 3 real-world comparison tiers: Economic, Moderate, Luxury"""
        n = int(str(memory.get("travelers", "1")) or "1")
        days = max(1, int(str(memory.get("days", "3")) or "3"))
        nights = days
        
        # TRANSPORT ESTIMATES (One-way total)
        # Economic: Sleeper train (~₹600 base + dist factor)
        t_eco = int((450 + distance_km * 0.9) * n)
        # Moderate: AC Train/Flight (~₹2500 base)
        t_mod = int((2800 + distance_km * 3.0) * n)
        # Luxury: Premium Flight (~₹5500 base)
        t_lux = int((6000 + distance_km * 4.5) * n)

        # HOTEL ESTIMATES (Total Stay)
        # Economic: ₹800/night
        h_eco = 850 * n * nights
        # Moderate: ₹4000/night
        h_mod = 4200 * n * nights
        # Luxury: ₹12500/night
        h_lux = 13500 * n * nights

        # FOOD & MISC
        o_eco = 450 * n * days
        o_mod = 1200 * n * days
        o_lux = 3500 * n * days

        return {
            "eco": t_eco + h_eco + o_eco,
            "mod": t_mod + h_mod + o_mod,
            "lux": t_lux + h_lux + o_lux
        }


# ─────────────────────────────────────────────
# Agent 4: Planning Agent (Gemini-powered)
# ─────────────────────────────────────────────
class PlanningAgent:
    def plan(self, memory: dict) -> list:
        if gemini_available:
            return self._plan_with_gemini(memory)
        return self._plan_fallback(memory)

    def _plan_with_gemini(self, memory: dict) -> list:
        days = max(1, int(str(memory.get('days', '3')) or '3'))
        total_b = int(str(memory.get('budget', '15000')).replace(',', ''))
        t_count = max(1, int(str(memory.get('travelers', '1'))))
        
        # Build strict dynamic JSON array string to explicitly force LLM to match the days count
        ex_array = "[\n"
        for i in range(1, days + 1):
            ex_array += f'  {{"day": {i}, "theme": "...", "places": ["Place 1", "Place 2"], "plan": "2-sentence desc"}}'
            if i < days: ex_array += ",\n"
        ex_array += "\n]"

        prompt = f"""
Create a highly realistic {days}-day India travel itinerary.
Destination: {memory.get('destination')}
Trip Type: {memory.get('trip_type', 'leisure')}
Travelers: {t_count}
Total Budget: ₹{total_b} (Very Important: Ensure all activities, dining, and transit loosely fit within roughly ₹{total_b // days} per day total).
Travel Date: {memory.get('date')}

Include REAL places, landmarks, local food, and authentic experiences.
Return ONLY a valid JSON array matching this exact structure with EXACTLY {days} items:
{ex_array}
"""
        raw = call_gemini(prompt)
        raw = re.sub(r"```json|```", "", raw).strip()
        try:
            result = json.loads(raw)
            if isinstance(result, list):
                return result
        except Exception as e:
            print(f"[PlanningAgent]: {e}")
        return self._plan_fallback(memory)

    def _plan_fallback(self, memory: dict) -> list:
        dest = memory.get("destination", "your destination")
        days = max(1, int(str(memory.get('days', '3')) or '3'))
        ttype = str(memory.get("trip_type", "leisure")).title()
        
        fallback = []
        for i in range(1, days + 1):
            if i == 1:
                theme = "Arrival & Settling In"
                plan = f"Arrive in {dest} and check in. Explore the neighbourhood and enjoy an authentic local dinner."
            elif i == days and days > 1:
                theme = "Leisurely Wrap-up"
                plan = "A relaxed morning with breakfast, souvenir shopping, and a comfortable journey home."
            else:
                theme = f"{ttype} — Day {i} Experience"
                plan = f"A packed day covering the top attractions {dest} is known for. Make the most of every moment."
            
            fallback.append({
                "day": i, 
                "theme": theme, 
                "places": ["Main Attraction", "Local Spot"], 
                "plan": plan
            })
            
        return fallback


# ─────────────────────────────────────────────
# Main Orchestrator
# ─────────────────────────────────────────────
class Orchestrator:
    def __init__(self):
        self.memory_agent = MemoryAgent()
        self.conv_agent = ConversationAgent()
        self.budget_agent = BudgetAgent()
        self.planning_agent = PlanningAgent()

    def process(self, text: str, session_memory: dict) -> dict:
        pending = session_memory.get("_pending_field", "")
        session_memory = self.memory_agent.process(text, session_memory, pending_field=pending)

        conv = self.conv_agent.get_next_question(session_memory, text)

        if conv["status"] == "incomplete":
            missing = self.conv_agent.get_missing(session_memory)
            session_memory["_pending_field"] = missing[0] if missing else ""
            return {
                "status": "incomplete",
                "message": conv["message"],
                "memory": session_memory
            }

        return self._generate_plan(session_memory)

    def _generate_plan(self, memory: dict) -> dict:
        origin = memory["origin"]
        destination = memory["destination"]
        origin_iata = memory.get("origin_iata") or get_iata(origin)
        dest_iata = memory.get("dest_iata") or get_iata(destination)
        origin_station = memory.get("origin_station") or get_station(origin)
        dest_station = memory.get("dest_station") or get_station(destination)
        date = memory["date"]
        travelers = max(1, int(memory.get("travelers", "1") or "1"))

        # Calculate budget per person and days for ML transport model
        raw_budget = str(memory.get("budget", "15000"))
        nums = re.findall(r'\d+', raw_budget.replace(",", ""))
        budget_val = int(nums[0]) if nums else 15000
        bpp = budget_val // travelers
        days_val = max(1, int(memory.get("days", "3") or "3"))

        allowed_modes = get_allowed_modes(origin, destination, budget_per_person=bpp, travel_days=days_val)
        budget_data = self.budget_agent.optimize(memory, allowed_modes)

        # Try real Amadeus flight data
        real_flights: list[dict[str, Any]] = []
        if "flight" in allowed_modes:
            try:
                from apis.flights import search_flights  # type: ignore[import]
                real_flights = search_flights(origin_iata, dest_iata, date, travelers)
            except Exception as e:
                print(f"[Flight API]: {e}")

        travel_options = self._build_travel_options(
            origin, destination, origin_iata, dest_iata,
            origin_station, dest_station, date, travelers,
            allowed_modes, budget_data, real_flights
        )

        nights = int(str(budget_data["nights"]))
        hotels = self._build_hotels(destination, budget_data, date=date, travelers=travelers, nights=nights)

        # Calculate comparison tiers ONLY for the UI table (do NOT overwrite primary plan budget)
        price_tiers = self.budget_agent.calculate_tiers(memory, estimate_distance(origin, destination))
        min_feasible = self.budget_agent.economic_adjust(memory, travel_options, hotels)
        
        # We attach the min_feasible to the response so the UI can show the comparison
        memory["min_budget_info"] = min_feasible
        
        itinerary = self.planning_agent.plan(memory)

        # Events / Activities via Gemini
        events = []
        if gemini_available:
            try:
                prompt_events = f"""
List exactly 3 items to do in {destination}: 1 Famous Place to Visit, 1 Good Cafe/Restaurant, and 1 Top Event or Activity. 
Return exactly this JSON array structure, nothing else:
[ {{"title": "Famous Place: [Name]", "description": "Short description", "price": "e.g. ₹500"}}, {{"title": "Cafe: [Name]", "description": "Short description", "price": "e.g. ₹800"}}, {{"title": "Activity: [Name]", "description": "Short description", "price": "Free"}} ]
"""
                ans_ev = call_gemini(prompt_events)
                if ans_ev:
                    import json
                    clean_ev = ans_ev.strip().replace('```json', '').replace('```', '').strip()
                    events = json.loads(clean_ev)
            except Exception:
                pass

        if not events:
            events = [
                {"title": f"Famous Place: Central {destination}", "description": "Walk around the city center and explore famous landmarks.", "price": "Free"},
                {"title": f"Cafe: Local Delight {destination}", "description": "Grab a coffee and taste regional authentic snacks.", "price": "₹600 approx"},
                {"title": f"Activity: {destination} Heritage Walk", "description": "Discover the vibrant local culture and history.", "price": "Variable"}
            ]

        # Travel tip via Gemini
        advisory = ""
        if gemini_available:
            tip = call_gemini(f"Give one practical travel tip for visiting {destination} in {date[:7]}. 1 sentence only.")
            advisory = tip

        return {
            "status": "complete",
            "message": f"Success! 💎 We've architected an elite itinerary tailored to your budget for your trip from {origin} to {destination}.",
            "trip_summary": {
                "from": origin,
                "to": destination,
                "date": date,
                "travelers": travelers,
                "distance_km": estimate_distance(origin, destination),
                "generated_at": "Updated just now",
                "allowed_modes": allowed_modes
            },
            "budget_breakdown": {
                "total": f"₹{budget_data['total']:,}",
                "transport": f"₹{budget_data['transport']:,}",
                "hotel": f"₹{budget_data['hotel']:,}",
                "food_misc": f"₹{budget_data['other']:,}",
                "per_person": f"₹{budget_data['per_person']:,}"
            },
            "price_tiers": {
                "economic": f"₹{price_tiers['eco']:,}",
                "moderate": f"₹{price_tiers['mod']:,}",
                "luxury": f"₹{price_tiers['lux']:,}"
            },
            "travel_options": travel_options,
            "hotels": hotels,
            "events": events,
            "itinerary": itinerary,
            "travel_advisory": advisory,
            "budget_warning": budget_data.get("warning", ""),
            "memory": memory
        }

    def _build_travel_options(
        self, origin: str, destination: str,
        o_iata: str, d_iata: str,
        o_station: str, d_station: str,
        date: str, travelers: int,
        allowed_modes: list[str], budget: dict[str, object],
        real_flights: list[dict[str, object]]
    ) -> list[dict[str, object]]:

        options: list[dict[str, object]] = []
        dp = date_parts(date)   # all date formats pre-computed
        
        dist = estimate_distance(origin, destination)
        from transport_ml import transport_ml  # type: ignore
        ml_prices = transport_ml.predict_prices(dist)

        o_slug = origin.lower().replace(" ", "-")
        d_slug = destination.lower().replace(" ", "-")
        pax_str = f"A-{travelers}_C-0_I-0"
        
        # Dynamically "search" for real operators
        flight_brand = "Multiple Airlines"
        train_brand = "Express/Mail Train"
        bus_brand = "Volvo AC/Sleeper Bus"
        if gemini_available:
            prompt = f"Name exactly 3 real options from {origin} to {destination} in India: 1 Airline, 1 Train name/number, and 1 Bus operator. If no direct, give best regional guess. Return ONLY a comma-separated list of the 3 names, nothing else."
            ans = call_gemini(prompt)
            if ans and "," in ans:
                parts = [p.strip().strip("'\"") for p in ans.split(",")]
                if len(parts) >= 3:
                    flight_brand = parts[0][:25]
                    train_brand = parts[1][:25]
                    bus_brand = parts[2][:25]

        # ──────── FLIGHT OPTIONS ────────
        total_trip_budget = int(str(budget["total"]))
        
        if "flight" in allowed_modes:
            # MakeMyTrip — verified URL format from live browser inspection
            # Format: /flight/search?itinerary={FROM}-{TO}-{DD/MM/YYYY}&tripType=O&paxType=A-N_C-0_I-0
            mmt_flight = (
                f"https://www.makemytrip.com/flight/search"
                f"?itinerary={o_iata.upper()}-{d_iata.upper()}-{dp['mmt_flight']}"
                f"&tripType=O&paxType={pax_str}&intl=false&cabinClass=E&lang=eng"
            )
            # Cleartrip — depart_date in DD-MM-YYYY
            cleartrip_flight = (
                f"https://www.cleartrip.com/flights/results/"
                f"?from={o_iata.upper()}&to={d_iata.upper()}"
                f"&depart_date={dp['redbus']}&adults={travelers}&class=Economy"
            )
            # Ixigo — date in DD-Mon-YYYY (e.g. 20-Apr-2026)
            ixigo_flight = (
                f"https://www.ixigo.com/search/result/flight"
                f"?from={o_iata.upper()}&to={d_iata.upper()}"
                f"&date={dp['ixigo']}&adults={travelers}&class=e&source=Search"
            )

            if real_flights:
                for i, fl in enumerate(real_flights):  # type: ignore
                    price = int(fl["price"]) # type: ignore[arg-type]
                    total = price * travelers
                    if total > total_trip_budget:
                        continue
                    badge = "fastest" if i == 0 else "cheapest"
                    stops = int(fl["stops"])  # type: ignore[arg-type]
                    stops_str = "Non-stop ✅" if stops == 0 else f"{stops} stop(s)"
                    options.append({
                        "type": badge,
                        "mode": f"Flight ✈️ ({fl['airline']})",
                        "cost_per_person": f"₹{price:,}",
                        "total_cost": f"₹{total:,}",
                        "duration": str(fl["duration"]),
                        "note": f"{stops_str} • Live data via Kiwi.com • {dp['dd']}/{dp['mm']}/{dp['yyyy']}",
                        "booking_link": mmt_flight,
                        "alt_links": [
                            {"label": "Cleartrip", "url": cleartrip_flight},
                            {"label": "Ixigo", "url": ixigo_flight},
                        ],
                        "platform": "MakeMyTrip"
                    })
            else:
                est_per_person = ml_prices["flight"]
                if (est_per_person * travelers) <= total_trip_budget:
                    options.append({
                        "type": "fastest",
                        "mode": f"Flight ✈️ ({flight_brand})",
                        "cost_per_person": f"₹{est_per_person:,}",
                        "total_cost": f"₹{est_per_person * travelers:,}",
                        "duration": "~1h 30m – 2h 30m",
                        "note": f"Suggested Option • Travel date: {dp['dd']}/{dp['mm']}/{dp['yyyy']}",
                        "booking_link": mmt_flight,
                        "alt_links": [
                            {"label": "Cleartrip", "url": cleartrip_flight},
                            {"label": "Ixigo", "url": ixigo_flight},
                        ],
                        "platform": "MakeMyTrip",
                    })

        # ──────── TRAIN OPTIONS ────────
        if "train" in allowed_modes:
            # IRCTC — date in YYYYMMDD
            irctc_link = (
                f"https://www.irctc.co.in/nget/train-search"
                f"?from={o_station}&to={d_station}&date={dp['irctc']}&class=SL"
            )
            # MakeMyTrip trains
            mmt_train = (
                f"https://www.makemytrip.com/railways/trainSearch.html"
                f"?from={o_station}&to={d_station}&date={dp['irctc']}"
            )
            # Ixigo trains
            ixigo_train = (
                f"https://www.ixigo.com/search/result/train"
                f"?from={o_station}&to={d_station}&date={dp['ixigo']}&class=SL"
            )
            train_cost = ml_prices["train"] * travelers
            if train_cost <= total_trip_budget:
                options.append({
                "type": "cheapest",
                "mode": f"Train 🚂 ({train_brand})",
                "cost_per_person": f"₹{(ml_prices['train']):,}",
                "total_cost": f"₹{train_cost:,}",
                "duration": "3AC / 2AC / CC",
                "note": f"Express service • Travel date: {dp['dd']}/{dp['mm']}/{dp['yyyy']}",
                "booking_link": irctc_link,
                "alt_links": [
                    {"label": "MakeMyTrip", "url": mmt_train},
                    {"label": "Ixigo", "url": ixigo_train},
                ],
                "platform": "IRCTC",
            })
            # ADDING NORMAL SLEEPER OPTION
            sleeper_pp = max(280, int(ml_prices['train'] * 0.55))
            sleeper_total = sleeper_pp * travelers
            if sleeper_total <= total_trip_budget:
                options.append({
                "type": "budget_extreme",
                "mode": "Normal Sleeper Train (Non-AC)",
                "cost_per_person": f"₹{(sleeper_pp):,}",
                "total_cost": f"₹{sleeper_total:,}",
                "duration": "Sleeper Class (SL)",
                "note": "Economical choice • Ideal for long distances on a budget",
                "booking_link": irctc_link,
                "alt_links": [
                    {"label": "ConfirmTkt", "url": "https://www.confirmtkt.com"},
                ],
                "platform": "IRCTC",
            })

        # ──────── BUS OPTIONS ────────
        if "bus" in allowed_modes:
            # redBus — date in DD-MM-YYYY
            redbus_link = (
                f"https://www.redbus.in/bus-tickets/{o_slug}-to-{d_slug}"
                f"?fromCityId=0&toCityId=0&onward={dp['redbus']}"
            )
            abhibus_link = f"https://www.abhibus.com/bus-tickets/{o_slug}-to-{d_slug}"
            mmt_bus = f"https://www.makemytrip.com/bus-tickets/{o_slug}-to-{d_slug}.html"
            bus_cost = ml_prices["bus"] * travelers
            if bus_cost <= total_trip_budget:
                options.append({
                "type": "budget",
                "mode": f"Bus 🚌 ({bus_brand})",
                "cost_per_person": f"₹{(ml_prices['bus']):,}",
                "total_cost": f"₹{bus_cost:,}",
                "duration": "AC Sleeper / Volvo available",
                "note": f"Multiple operators • Travel date: {dp['dd']}/{dp['mm']}/{dp['yyyy']}",
                "booking_link": redbus_link,
                "alt_links": [
                    {"label": "Abhibus", "url": abhibus_link},
                    {"label": "MakeMyTrip", "url": mmt_bus},
                ],
                "platform": "redBus",
            })

        if not options:
            options.append({
                "type": "warning",
                "mode": "⚠️ Budget Increase Required",
                "cost_per_person": "Exceeds Plan",
                "total_cost": "N/A",
                "duration": "Multiple Days",
                "note": f"We couldn't find any travel options from {origin} to {destination} within your specified budget. Please increase your budget by ₹2,000 to ₹5,000 for better results.",
                "booking_link": "#",
                "alt_links": [],
                "platform": "System Advisor"
            })
            
        return options

    def _build_hotels(self, destination: str, budget: dict[str, object], date: str = "", travelers: int = 1, nights: int = 3) -> list[dict[str, object]]:
        ppn: int = int(budget["hotel"]) // max(1, int(budget["nights"]))  # type: ignore[arg-type]
        slug = destination.lower().replace(" ", "-")
        mmt_city = get_mmt_city(destination)
        dp = date_parts(date) if date else {}

        checkin  = dp.get("mmt_hotel", "")  # MMDDYYYY
        # checkout = checkin + nights days
        checkout = ""
        if date:
            try:
                from datetime import datetime, timedelta
                ci = datetime.strptime(date, "%Y-%m-%d")
                co = ci + timedelta(days=nights)
                checkout = co.strftime("%m%d%Y")
            except Exception:
                pass

        # MakeMyTrip hotel-listing with city code + dates + pax
        mmt_hotel = (
            f"https://www.makemytrip.com/hotels/hotel-listing/"
            f"?city={mmt_city}&roomCount=1&adult={travelers}&children=0"
            + (f"&checkin={checkin}&checkout={checkout}" if checkin else "")
        )
        # Goibibo hotel search
        goibibo_hotel = (
            f"https://www.goibibo.com/hotels/hotels-in-{slug}/"
            + (f"?checkin={checkin}&checkout={checkout}&adults={travelers}&rooms=1" if checkin else "")
        )
        # Cleartrip hotel
        cleartrip_hotel = (
            f"https://www.cleartrip.com/hotels/in/{slug}/"
            + (f"?checkin={checkin}&checkout={checkout}&adults={travelers}&rooms=1" if checkin else "")
        )

        # Determine realistic categories based on ppn
        is_tight = budget.get("is_deficit", False)
        
        if ppn < 1500 or is_tight:
            # Force low-cost survival options if budget is tight or low
            cats = ["Survival Hostel / Dorms", "Budget Saver Room", "Comfort 3-Star"]
            prices = [max(350, ppn // 3), max(800, ppn), int(ppn * 1.5)]
            emojis = ["🎒", "🟢", "🟡"]
        elif ppn < 4000:
            cats = ["Budget Saver", "Comfort 3-Star", "Premium 4-Star"]
            prices = [max(1000, ppn - 1000), ppn, int(ppn * 1.5)]
            emojis = ["🟢", "🟡", "🌟"]
        elif ppn < 10000:
            cats = ["Standard 3-Star", "Premium 4-Star", "Luxury 5-Star"]
            prices = [max(2500, ppn - 2500), ppn, int(ppn * 1.5)]
            emojis = ["🟡", "🌟", "👑"]
        else:
            cats = ["Premium 4-Star", "Luxury 5-Star", "Elite Resort"]
            prices = [max(5000, ppn - 4000), ppn, int(ppn * 1.5)]
            emojis = ["🌟", "👑", "💎"]
            
        # Get real hotel names matching these exact prices via the new predictive ML Model
        from transport_ml import hotel_predictor  # type: ignore
        h_names = [
            hotel_predictor.predict_hotel(destination, prices[0]),
            hotel_predictor.predict_hotel(destination, prices[1]),
            hotel_predictor.predict_hotel(destination, prices[2])
        ]
                    
        import urllib.parse
        options: list[dict[str, object]] = []
        for i in range(3):
            hn = h_names[i]  # type: ignore
            
            # MakeMyTrip specific search link targeting this EXACT hotel
            query_enc = urllib.parse.quote(f"{hn} {destination}")
            mmt_specific_link = (
                f"https://www.makemytrip.com/hotels/hotel-listing/"
                f"?city={mmt_city}&searchText={query_enc}&roomCount=1&adult={travelers}&children=0"
            )
            if checkin:
                mmt_specific_link += f"&checkin={checkin}&checkout={checkout}"
                
            # Create a Google Booking search link as an alternate option
            g_query = urllib.parse.quote(f"Book {hn} in {destination}")
            google_link = f"https://www.google.com/search?q={g_query}"
            
            total_stay = prices[i] * max(1, nights)
            options.append({
                "category": cats[i], "emoji": emojis[i],
                "name": hn,
                "price_per_night": f"₹{prices[i]:,}",
                "total_stay_price": f"₹{total_stay:,} for {nights} night" + ("s" if nights > 1 else ""),
                "location": f"Top Rated in {destination}" if i > 0 else f"Budget Location, {destination}",
                "booking_link": mmt_specific_link,
                "alt_links": [
                    {"label": "Google Options", "url": google_link},
                ], # type: ignore[list-item]
            })

        return options

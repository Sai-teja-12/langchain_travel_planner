import json
import os
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_core.tools import tool
from serpapi import GoogleSearch

load_dotenv()


def _simplify_flight(flight: dict, *, include_token: bool = False) -> dict:
    """Extract a compact summary from a SerpAPI Google Flights result."""
    flights = flight.get("flights") or []
    first_leg = flights[0] if flights else {}
    last_leg = flights[-1] if flights else {}
    airlines = list(
        dict.fromkeys(
            leg.get("airline") for leg in flights if leg.get("airline")
        )
    )
    flight_numbers = [
        leg.get("flight_number") for leg in flights if leg.get("flight_number")
    ]
    summary: dict[str, Any] = {
        "price": flight.get("price"),
        "total_duration": flight.get("total_duration"),
        "airline": " / ".join(airlines) if airlines else first_leg.get("airline"),
        "flight_number": first_leg.get("flight_number"),
        "flight_numbers": flight_numbers,
        "departure_airport": (first_leg.get("departure_airport") or {}).get("id"),
        "arrival_airport": (last_leg.get("arrival_airport") or {}).get("id"),
        "departure_time": (first_leg.get("departure_airport") or {}).get("time"),
        "arrival_time": (last_leg.get("arrival_airport") or {}).get("time"),
        "layovers": len(flight.get("layovers") or []),
        "type": flight.get("type"),
    }
    if include_token and flight.get("departure_token"):
        summary["departure_token"] = flight["departure_token"]
    return summary


def _google_flights_search(params: dict) -> dict:
    data = GoogleSearch(params).get_dict()
    if data.get("error"):
        return {"error": data["error"]}
    return data


def _collect_flights(data: dict, limit: int = 8) -> list[dict]:
    """Merge best + other flights, sort by price, keep cheapest first."""
    flights = list(data.get("best_flights") or []) + list(data.get("other_flights") or [])
    priced = [f for f in flights if f.get("price") is not None]
    unpriced = [f for f in flights if f.get("price") is None]
    priced.sort(key=lambda f: f["price"])
    return (priced + unpriced)[:limit]


@tool
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    travelers: int = 1,
) -> str:
    """Search for flights via SerpAPI Google Flights.

    For round trips (when return_date is set), also fetches return-date flights
    for the cheapest outbound option. Return-flight prices are total round-trip
    prices for that outbound + return pair.

    IMPORTANT: `price` values are the TOTAL fare for ALL adults in `travelers`
    (not per-person), and for round trips they are ROUND-TRIP totals.

    Args:
        origin: Departure airport IATA code (e.g. "JFK")
        destination: Arrival airport IATA code (e.g. "NRT")
        departure_date: Outbound date in YYYY-MM-DD format
        return_date: Optional return date in YYYY-MM-DD format for round trips
        travelers: Number of adult passengers
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return json.dumps({"error": "SERPAPI_API_KEY not set. Use your own knowledge."})

    adults = max(1, travelers)
    try:
        params: dict = {
            "engine": "google_flights",
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": departure_date,
            "adults": adults,
            "currency": "USD",
            "hl": "en",
            "gl": os.getenv("SERPAPI_GL", "in"),
            "api_key": api_key,
        }
        if return_date:
            params["return_date"] = return_date
            params["type"] = "1"  # round trip
        else:
            params["type"] = "2"  # one way

        data = _google_flights_search(params)
        if data.get("error"):
            return json.dumps({"error": data["error"]})

        outbound_raw = _collect_flights(data, limit=8)
        outbound = [_simplify_flight(f, include_token=bool(return_date)) for f in outbound_raw]

        price_insights = data.get("price_insights") or {}
        result: dict[str, Any] = {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date,
            "return_date": return_date,
            "travelers": adults,
            "price_basis": (
                f"TOTAL for {adults} adult(s); "
                + ("round-trip" if return_date else "one-way")
            ),
            "lowest_price_insight": price_insights.get("lowest_price"),
            "outbound_flights": outbound,
            "return_flights": [],
        }

        if return_date:
            # Prefer the cheapest outbound that has a departure_token
            selected = next(
                (f for f in outbound_raw if f.get("departure_token")),
                None,
            )
            if selected is not None:
                return_params = {
                    **params,
                    "departure_token": selected["departure_token"],
                }
                return_data = _google_flights_search(return_params)
                if return_data.get("error"):
                    result["return_flights_error"] = return_data["error"]
                else:
                    return_raw = _collect_flights(return_data, limit=8)
                    result["selected_outbound"] = _simplify_flight(selected)
                    result["return_flights"] = [
                        _simplify_flight(f) for f in return_raw
                    ]
                    result["pricing_note"] = (
                        "All prices are TOTAL for all travelers (not per-person) "
                        "and are already ROUND-TRIP. "
                        "Copy outbound_flights[].price onto outbound options only. "
                        "Return options must use price=0 — do NOT copy "
                        "return_flights[].price (same round-trip package again). "
                        "Budget = cheapest outbound price once; never add outbound+return."
                    )
            else:
                result["return_flights_error"] = (
                    "No departure_token on outbound results; could not fetch return flights."
                )

        return json.dumps(result)
    except Exception as exc:
        return json.dumps({"error": f"Flight search failed: {exc}"})

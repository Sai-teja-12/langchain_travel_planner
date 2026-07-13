import json
import os
from typing import Optional

import googlemaps
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()


@tool
def search_places(query: str, place_type: Optional[str] = None) -> str:
    """Search Google Places for hotels, restaurants, attractions, or other locations.

    Args:
        query: Text search query, e.g. "hotels near Shinjuku Tokyo" or "best ramen Shibuya"
        place_type: Optional Places type filter, e.g. "lodging", "restaurant", "tourist_attraction"
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return json.dumps(
            {"error": "GOOGLE_MAPS_API_KEY not set. Use your own knowledge."}
        )

    try:
        client = googlemaps.Client(key=api_key)
        kwargs: dict = {"query": query}
        if place_type:
            kwargs["type"] = place_type
        data = client.places(**kwargs)

        places = []
        for result in data.get("results", [])[:10]:
            places.append(
                {
                    "name": result.get("name"),
                    "address": result.get("formatted_address"),
                    "rating": result.get("rating"),
                    "user_ratings_total": result.get("user_ratings_total"),
                    "types": result.get("types", [])[:5],
                    "place_id": result.get("place_id"),
                    "price_level": result.get("price_level"),
                }
            )

        return json.dumps({"places": places, "status": data.get("status")})
    except Exception as exc:
        return json.dumps({"error": f"Places search failed: {exc}"})

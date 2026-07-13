import json
import os
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from src.config.model_provider import create_model
from src.models.schemas import (
    DayItinerary,
    FlightOption,
    HotelOption,
    TravelRequest,
)
from src.tools.google_maps import search_places
from src.tools.web_search import web_search
from src.utils.agent_loop import run_agent_loop
from src.utils.json_utils import parse_structured_list

_ITINERARY_SCHEMA = json.dumps(DayItinerary.model_json_schema(), indent=2)

SYSTEM_PROMPT = f"""You are an itinerary planning specialist.
Use search_places and web_search to find attractions, restaurants, and activities.
Build a realistic day-by-day plan for the trip dates.

Return ONLY a JSON array of day itineraries. No markdown, no explanation.
Each object must match this schema:
{_ITINERARY_SCHEMA}

Cover every day from departure to return. Balance morning/afternoon/evening when possible.
If tools fail, plan from your own knowledge using the same JSON schema.
"""


async def run_itinerary_agent(
    request: TravelRequest,
    destination_info: Optional[str] = None,
    flights: Optional[List[FlightOption]] = None,
    hotels: Optional[List[HotelOption]] = None,
) -> List[DayItinerary]:
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = create_model(temperature=0.3, provider=provider)

    context_parts = [
        f"Destination: {request.destination}",
        f"Origin: {request.origin}",
        f"Dates: {request.departure_date} to {request.return_date}",
        f"Travelers: {request.travelers}",
        f"Preferences: {request.preferences or 'none'}",
    ]
    if destination_info:
        context_parts.append(f"Destination research:\n{destination_info}")
    if flights:
        context_parts.append(
            "Flights:\n"
            + json.dumps([f.model_dump() for f in flights], indent=2)
        )
    if hotels:
        context_parts.append(
            "Hotels:\n" + json.dumps([h.model_dump() for h in hotels], indent=2)
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="\n\n".join(context_parts)),
    ]
    raw = await run_agent_loop(
        model, [search_places, web_search], messages, max_iter=7,
        agent_name="itinerary-planner",
    )
    return parse_structured_list(raw, DayItinerary)  # type: ignore[return-value]

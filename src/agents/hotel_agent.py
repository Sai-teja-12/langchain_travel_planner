import json
import os
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from src.config.model_provider import create_model
from src.models.schemas import HotelOption, TravelRequest
from src.tools.google_maps import search_places
from src.tools.web_search import web_search
from src.utils.agent_loop import run_agent_loop
from src.utils.json_utils import parse_structured_list

_HOTEL_SCHEMA = json.dumps(HotelOption.model_json_schema(), indent=2)

SYSTEM_PROMPT = f"""You are a hotel search specialist.
Use search_places (type lodging when useful) and web_search to find hotels near the destination.

Return ONLY a JSON array of 3-5 hotel options. No markdown, no explanation.
Each object must match this schema:
{_HOTEL_SCHEMA}

If tools fail, estimate plausible options from your knowledge using the same JSON schema.
`price_per_night` and `rating` must be numbers.
"""


async def run_hotel_agent(request: TravelRequest) -> List[HotelOption]:
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = create_model(temperature=0, provider=provider)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Find hotels in: {request.destination}\n"
                f"Check-in: {request.departure_date}\n"
                f"Check-out: {request.return_date}\n"
                f"Travelers: {request.travelers}\n"
                f"Budget: {request.budget if request.budget is not None else 'not specified'}\n"
                f"Preferences: {request.preferences or 'none'}"
            )
        ),
    ]
    raw = await run_agent_loop(
        model, [search_places, web_search], messages, max_iter=6,
        agent_name="hotel-search",
    )
    return parse_structured_list(raw, HotelOption)  # type: ignore[return-value]

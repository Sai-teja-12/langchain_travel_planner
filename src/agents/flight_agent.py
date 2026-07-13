import json
import os
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from src.config.model_provider import create_model
from src.models.schemas import FlightOption, TravelRequest
from src.tools.flights import search_flights
from src.tools.web_search import web_search
from src.utils.agent_loop import run_agent_loop
from src.utils.json_utils import parse_structured_list

_FLIGHT_SCHEMA = json.dumps(FlightOption.model_json_schema(), indent=2)

SYSTEM_PROMPT = f"""You are a flight search specialist.
Use search_flights to find real options, and web_search if you need airport codes or airline context.

Always search as a round trip when a return date is provided. Pass travelers exactly
as given. The tool returns both outbound_flights and return_flights — you MUST include
both directions in your output.

Return ONLY a JSON array of flight options (typically 2-3 outbound + 2-3 return).
No markdown, no explanation.
Each object must match this schema:
{_FLIGHT_SCHEMA}

Rules:
- Set direction to "outbound" for departure-date flights (origin → destination).
- Set direction to "return" for return-date flights (destination → origin).
- ALWAYS include the cheapest outbound and cheapest return from the tool results.
  Do not skip low-cost carriers or codeshare options.
- CRITICAL PRICING (SerpAPI prices are already ROUND-TRIP totals for all travelers):
  - Outbound options: copy the tool's round-trip `price` as-is.
  - Return options: set `price` to 0. Do NOT copy return_flights[].price — that is
    the same round-trip package again and would double-count.
- If tools fail, estimate one-way outbound and one-way return separately (both > 0).
"""


async def run_flight_agent(request: TravelRequest) -> List[FlightOption]:
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = create_model(temperature=0, provider=provider)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Find round-trip flights (outbound AND return):\n"
                f"Origin: {request.origin}\n"
                f"Destination: {request.destination}\n"
                f"Departure: {request.departure_date}\n"
                f"Return: {request.return_date}\n"
                f"Travelers: {request.travelers}\n"
                f"Budget: {request.budget if request.budget is not None else 'not specified'}\n"
                f"Preferences: {request.preferences or 'none'}\n\n"
                f"Include the cheapest options. Put the round-trip total ONLY on "
                f"outbound rows; return rows must have price=0."
            )
        ),
    ]
    raw = await run_agent_loop(
        model,
        [search_flights, web_search],
        messages,
        max_iter=6,
        agent_name="flight-search",
    )
    flights = parse_structured_list(raw, FlightOption)  # type: ignore[return-value]
    return _dedupe_round_trip_prices(flights)


def _dedupe_round_trip_prices(flights: List[FlightOption]) -> List[FlightOption]:
    """Ensure return legs do not carry a second copy of the round-trip fare."""
    outbounds = [f for f in flights if f.direction != "return"]
    returns = [f for f in flights if f.direction == "return"]
    if not outbounds or not returns:
        return flights

    # If any return still has a positive price, zero them — SerpAPI RT fare
    # already lives on outbound options.
    if any(f.price > 0 for f in returns) and any(f.price > 0 for f in outbounds):
        returns = [
            f.model_copy(update={"price": 0.0}) for f in returns
        ]
    return outbounds + returns

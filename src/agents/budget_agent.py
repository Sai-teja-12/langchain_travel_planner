import json
import os
from datetime import datetime
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from src.config.model_provider import create_model
from src.models.schemas import (
    BudgetBreakdown,
    DayItinerary,
    FlightOption,
    HotelOption,
    TravelRequest,
)
from src.utils.agent_loop import run_agent_loop
from src.utils.json_utils import parse_structured_output

_BUDGET_SCHEMA = json.dumps(BudgetBreakdown.model_json_schema(), indent=2)

SYSTEM_PROMPT = f"""You are a travel budget calculator.
You do not need tools — compute hotels and activities from the provided data.
flights_cost will be filled in by the system; you may set it to 0.

Rules:
- hotels_cost: price_per_night x number of nights x number of rooms
  (assume 1 room per 2 travelers unless stated otherwise)
- activities_cost: sum activity costs across the itinerary
  (scale by travelers if costs look clearly per-person)
- flights_cost: set to 0 (overridden deterministically)
- total_cost: hotels_cost + activities_cost (flights added later)

Return ONLY a JSON object matching this schema. No markdown, no explanation:
{_BUDGET_SCHEMA}
"""


def round_trip_flights_cost(flights: List[FlightOption]) -> float:
    """
    SerpAPI round-trip fares are stored once on outbound options (return price=0).
    Use the cheapest positive outbound fare. If only returns have prices (legacy),
    use the cheapest return once — never sum outbound + return.
    """
    outbounds = [f.price for f in flights if f.direction != "return" and f.price > 0]
    returns = [f.price for f in flights if f.direction == "return" and f.price > 0]
    if outbounds:
        return min(outbounds)
    if returns:
        return min(returns)
    return 0.0


def _nights(departure_date: str, return_date: str) -> int:
    try:
        start = datetime.strptime(departure_date, "%Y-%m-%d")
        end = datetime.strptime(return_date, "%Y-%m-%d")
        return max(1, (end - start).days)
    except ValueError:
        return 1


async def run_budget_agent(
    request: TravelRequest,
    flights: List[FlightOption],
    hotels: List[HotelOption],
    itinerary: List[DayItinerary],
) -> BudgetBreakdown:
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = create_model(temperature=0, provider=provider)
    nights = _nights(request.departure_date, request.return_date)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Travelers: {request.travelers}\n"
                f"Dates: {request.departure_date} to {request.return_date} "
                f"({nights} night(s))\n"
                f"Budget cap: {request.budget if request.budget is not None else 'none'}\n\n"
                f"Hotels:\n{json.dumps([h.model_dump() for h in hotels], indent=2)}\n\n"
                f"Itinerary:\n{json.dumps([d.model_dump() for d in itinerary], indent=2)}"
            )
        ),
    ]
    raw = await run_agent_loop(
        model, [], messages, max_iter=2, agent_name="budget-calculator"
    )
    budget = parse_structured_output(raw, BudgetBreakdown)  # type: ignore[return-value]

    flights_cost = round_trip_flights_cost(flights)
    hotels_cost = budget.hotels_cost
    activities_cost = budget.activities_cost
    return BudgetBreakdown(
        flights_cost=flights_cost,
        hotels_cost=hotels_cost,
        activities_cost=activities_cost,
        total_cost=flights_cost + hotels_cost + activities_cost,
    )

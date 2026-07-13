"""LangGraph orchestration for the multi-agent travel planner."""

from __future__ import annotations

import operator
import os
from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from src.agents.budget_agent import run_budget_agent
from src.agents.destination_research_agent import run_destination_research_agent
from src.agents.flight_agent import run_flight_agent
from src.agents.hotel_agent import run_hotel_agent
from src.agents.itinerary_agent import run_itinerary_agent
from src.config.model_provider import create_model
from src.models.schemas import (
    BudgetBreakdown,
    DayItinerary,
    FlightOption,
    HotelOption,
    TravelRequest,
    TripPlan,
)
from src.utils.agent_loop import message_content_to_text
from src.utils.json_utils import extract_json_array

class TravelState(TypedDict):
    request: TravelRequest
    destination_info: Optional[str]
    flights: Optional[List[FlightOption]]
    hotels: Optional[List[HotelOption]]
    itinerary: Optional[List[DayItinerary]]
    budget: Optional[BudgetBreakdown]
    final_plan: Optional[TripPlan]
    # Parallel nodes can each append without last-write-wins loss
    errors: Annotated[List[str], operator.add]


async def destination_research_node(state: TravelState) -> dict:
    try:
        destination_info = await run_destination_research_agent(state["request"])
        return {"destination_info": destination_info}
    except Exception as err:
        return {"errors": [f"DestinationAgent: {err}"]}


async def flight_search_node(state: TravelState) -> dict:
    try:
        flights = await run_flight_agent(state["request"])
        return {"flights": flights}
    except Exception as err:
        return {"errors": [f"FlightAgent: {err}"]}


async def hotel_search_node(state: TravelState) -> dict:
    try:
        hotels = await run_hotel_agent(state["request"])
        return {"hotels": hotels}
    except Exception as err:
        return {"errors": [f"HotelAgent: {err}"]}


async def itinerary_planner_node(state: TravelState) -> dict:
    try:
        itinerary = await run_itinerary_agent(
            state["request"],
            destination_info=state.get("destination_info"),
            flights=state.get("flights"),
            hotels=state.get("hotels"),
        )
        return {"itinerary": itinerary}
    except Exception as err:
        return {"errors": [f"ItineraryAgent: {err}"]}


async def budget_calculator_node(state: TravelState) -> dict:
    try:
        budget = await run_budget_agent(
            state["request"],
            flights=state.get("flights") or [],
            hotels=state.get("hotels") or [],
            itinerary=state.get("itinerary") or [],
        )
        return {"budget": budget}
    except Exception as err:
        return {"errors": [f"BudgetAgent: {err}"]}


def _serialize_state_for_prompt(state: TravelState) -> str:
    """Full TravelState snapshot for assemble prompts (and LangSmith traces)."""
    request = state["request"]
    flights = state.get("flights") or []
    hotels = state.get("hotels") or []
    itinerary = state.get("itinerary") or []
    budget = state.get("budget")
    errors = state.get("errors") or []

    parts = [
        f"Trip: {request.origin} → {request.destination}",
        f"Dates: {request.departure_date} to {request.return_date}",
        f"Travelers: {request.travelers}",
        f"Budget cap: {request.budget if request.budget is not None else 'none'}",
        f"Preferences: {request.preferences or 'none'}",
        f"\nDestination research:\n{state.get('destination_info') or '(none)'}",
        "\nFlights:\n"
        + (
            "\n".join(
                f"- [{getattr(f, 'direction', 'outbound')}] {f.airline} {f.flight_number} "
                f"{f.departure_airport}→{f.arrival_airport} ${f.price}"
                for f in flights
            )
            or "(none)"
        ),
        "\nHotels:\n"
        + (
            "\n".join(
                f"- {h.name} ★{h.rating} ${h.price_per_night}/night — {h.address}"
                for h in hotels
            )
            or "(none)"
        ),
        "\nItinerary:\n"
        + (
            "\n".join(
                f"- {day.date}: "
                + "; ".join(f"{a.name} (${a.cost})" for a in day.activities)
                for day in itinerary
            )
            or "(none)"
        ),
    ]
    if budget is not None:
        parts.append(
            "\nBudget breakdown:\n"
            f"- Flights: ${budget.flights_cost}\n"
            f"- Hotels: ${budget.hotels_cost}\n"
            f"- Activities: ${budget.activities_cost}\n"
            f"- Total: ${budget.total_cost}"
        )
    if errors:
        parts.append("\nUpstream warnings:\n" + "\n".join(f"- {e}" for e in errors))
    return "\n".join(parts)


async def assemble_node(state: TravelState) -> dict:
    """Two direct Gemini calls (no ReAct loop): trip summary + travel tips."""
    try:
        provider = os.getenv("LLM_PROVIDER", "gemini")
        state_snapshot = _serialize_state_for_prompt(state)

        summary_model = create_model(temperature=0.4, provider=provider)
        summary_res = await summary_model.ainvoke(
            [
                SystemMessage(
                    content=(
                        "You are a professional travel writer. Write a compelling "
                        "5-7 sentence trip summary that captures the essence and "
                        "excitement of the destination. Ground the summary in the "
                        "full trip context provided (research, flights, hotels, "
                        "itinerary, budget) — do not invent details that contradict it."
                    )
                ),
                HumanMessage(content=state_snapshot),
            ]
        )

        tips_model = create_model(temperature=0, provider=provider)
        tips_res = await tips_model.ainvoke(
            [
                SystemMessage(
                    content=(
                        "Give exactly 5 practical travel tips as a JSON array of strings. "
                        "Base them on the destination research and trip context below. "
                        "Return ONLY the JSON array, no explanation, no markdown."
                    )
                ),
                HumanMessage(content=state_snapshot),
            ]
        )

        travel_tips = [
            str(tip)
            for tip in extract_json_array(message_content_to_text(tips_res.content))
        ]
        budget = state.get("budget") or BudgetBreakdown(
            flights_cost=0.0,
            hotels_cost=0.0,
            activities_cost=0.0,
            total_cost=0.0,
        )

        return {
            "final_plan": TripPlan(
                summary=message_content_to_text(summary_res.content),
                flights=state.get("flights") or [],
                hotels=state.get("hotels") or [],
                itinerary=state.get("itinerary") or [],
                budget=budget,
                travel_tips=travel_tips,
            )
        }
    except Exception as err:
        return {"errors": [f"AssembleNode: {err}"]}


def build_travel_planner_graph():
    """Wire the StateGraph per Architecture Diagram 1 and return a compiled graph."""
    graph = StateGraph(TravelState)

    graph.add_node("destination_research", destination_research_node)
    graph.add_node("flight_search", flight_search_node)
    graph.add_node("hotel_search", hotel_search_node)
    graph.add_node("itinerary_planner", itinerary_planner_node)
    graph.add_node("budget_calculator", budget_calculator_node)
    graph.add_node("assemble", assemble_node)

    # Fan-out — three agents run in parallel
    graph.add_edge(START, "destination_research")
    graph.add_edge(START, "flight_search")
    graph.add_edge(START, "hotel_search")

    # Fan-in — itinerary waits for all three
    graph.add_edge("destination_research", "itinerary_planner")
    graph.add_edge("flight_search", "itinerary_planner")
    graph.add_edge("hotel_search", "itinerary_planner")

    graph.add_edge("itinerary_planner", "budget_calculator")
    graph.add_edge("budget_calculator", "assemble")
    graph.add_edge("assemble", END)

    return graph.compile()

"""CLI entry point — collect a TravelRequest, stream graph progress, print TripPlan."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date, datetime
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()


from src.graph.travel_planner_graph import build_travel_planner_graph
from src.models.schemas import TravelRequest, TripPlan

NODE_LABELS = {
    "destination_research": "Destination researched",
    "flight_search": "Flights searched",
    "hotel_search": "Hotels searched",
    "itinerary_planner": "Itinerary built",
    "budget_calculator": "Budget calculated",
    "assemble": "Trip plan assembled",
}


def _prompt(label: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{label}{suffix}: ").strip()
    if value:
        return value
    if default is not None:
        return default
    raise SystemExit(f"Required: {label}")


def _prompt_optional(label: str) -> Optional[str]:
    value = input(f"{label} (optional): ").strip()
    return value or None


def _parse_date(value: str, field: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"{field} must be YYYY-MM-DD, got: {value}") from exc
    return value


def build_request_from_args(argv: Optional[List[str]] = None) -> TravelRequest:
    parser = argparse.ArgumentParser(
        description="Multi-agent travel planner (LangGraph + Gemini)",
    )
    parser.add_argument("--origin", help="Departure city or IATA code (e.g. BLR)")
    parser.add_argument("--destination", help="Arrival city or IATA code (e.g. FCO)")
    parser.add_argument("--departure-date", help="Departure date YYYY-MM-DD")
    parser.add_argument("--return-date", help="Return date YYYY-MM-DD")
    parser.add_argument("--travelers", type=int, help="Number of travelers")
    parser.add_argument("--budget", type=float, help="Optional max budget")
    parser.add_argument("--preferences", help="Optional preferences")
    args = parser.parse_args(argv)

    interactive = not all(
        [
            args.origin,
            args.destination,
            args.departure_date,
            args.return_date,
        ]
    )
    if interactive:
        print("Travel planner — enter trip details (blank uses default where shown)\n")

    today = date.today().isoformat()
    origin = args.origin or _prompt("Origin (city or IATA)")
    destination = args.destination or _prompt("Destination (city or IATA)")
    departure_date = _parse_date(
        args.departure_date or _prompt("Departure date (YYYY-MM-DD)", today),
        "departure_date",
    )
    return_date = _parse_date(
        args.return_date or _prompt("Return date (YYYY-MM-DD)"),
        "return_date",
    )

    if args.travelers is not None:
        travelers = args.travelers
    elif interactive:
        raw = _prompt("Travelers", "1")
        try:
            travelers = int(raw)
        except ValueError as exc:
            raise SystemExit(f"travelers must be an integer, got: {raw}") from exc
    else:
        travelers = 1

    if args.budget is not None:
        budget = args.budget
    elif interactive:
        raw_budget = _prompt_optional("Budget")
        budget = float(raw_budget) if raw_budget else None
    else:
        budget = None

    if args.preferences is not None:
        preferences = args.preferences
    elif interactive:
        preferences = _prompt_optional("Preferences")
    else:
        preferences = None

    return TravelRequest(
        origin=origin.upper() if len(origin) == 3 else origin,
        destination=destination.upper() if len(destination) == 3 else destination,
        departure_date=departure_date,
        return_date=return_date,
        travelers=travelers,
        budget=budget,
        preferences=preferences,
    )


def _print_flights(plan: TripPlan) -> None:
    print("\n── Flights ──")
    if not plan.flights:
        print("  (none)")
        return
    has_priced_outbound = any(
        (getattr(f, "direction", "outbound") or "outbound") != "return" and f.price > 0
        for f in plan.flights
    )
    for i, f in enumerate(plan.flights, 1):
        direction = getattr(f, "direction", "outbound") or "outbound"
        label = "OUT" if direction == "outbound" else "RET"
        schedule = (
            f"{f.airline} {f.flight_number}  "
            f"{f.departure_airport}→{f.arrival_airport}  "
            f"{f.departure_time}→{f.arrival_time}"
        )
        if direction == "return" and has_priced_outbound:
            # Round-trip fare already shown on outbound options
            price_str = "(RT fare on outbound)"
        elif f.price > 0:
            price_str = f"${f.price:,.2f} RT"
        else:
            price_str = "(no price)"
        print(f"  {i}. [{label}] {schedule}  {price_str}")


def _print_hotels(plan: TripPlan) -> None:
    print("\n── Hotels ──")
    if not plan.hotels:
        print("  (none)")
        return
    for i, h in enumerate(plan.hotels, 1):
        print(
            f"  {i}. {h.name}  ★{h.rating:.1f}  "
            f"${h.price_per_night:,.2f}/night\n"
            f"     {h.address}"
        )


def _print_itinerary(plan: TripPlan) -> None:
    print("\n── Itinerary ──")
    if not plan.itinerary:
        print("  (none)")
        return
    for day in plan.itinerary:
        print(f"\n  {day.date}")
        for act in day.activities:
            print(f"    • {act.name} (${act.cost:,.2f})")
            if act.description:
                print(f"      {act.description}")


def _print_budget(plan: TripPlan) -> None:
    b = plan.budget
    print("\n── Budget ──")
    print(f"  Flights:     ${b.flights_cost:,.2f}")
    print(f"  Hotels:      ${b.hotels_cost:,.2f}")
    print(f"  Activities:  ${b.activities_cost:,.2f}")
    print(f"  Total:       ${b.total_cost:,.2f}")


def _print_tips(plan: TripPlan) -> None:
    print("\n── Travel tips ──")
    if not plan.travel_tips:
        print("  (none)")
        return
    for i, tip in enumerate(plan.travel_tips, 1):
        print(f"  {i}. {tip}")


def print_trip_plan(plan: TripPlan, request: TravelRequest) -> None:
    header = f"{request.origin} → {request.destination}"
    dates = f"{request.departure_date} to {request.return_date}"
    print("\n" + "═" * 50)
    print(f"  {header}  |  {dates}  |  {request.travelers} traveler(s)")
    print("═" * 50)
    print(f"\n{plan.summary}")
    _print_flights(plan)
    _print_hotels(plan)
    _print_itinerary(plan)
    _print_budget(plan)
    _print_tips(plan)
    print()


async def run_planner(request: TravelRequest) -> None:
    graph = build_travel_planner_graph()
    final_plan: Optional[TripPlan] = None
    errors: List[str] = []

    print("\nPlanning your trip...\n")

    async for event in graph.astream_events(
        {"request": request, "errors": []},
        version="v2",
    ):
        metadata = event.get("metadata") or {}
        node_name = metadata.get("langgraph_node") or ""
        if event.get("event") != "on_chain_end" or node_name not in NODE_LABELS:
            continue

        print(f"  ✓  {NODE_LABELS[node_name]}")

        output = event.get("data", {}).get("output") or {}
        if isinstance(output, dict):
            for err in output.get("errors") or []:
                errors.append(str(err))
            if node_name == "assemble" and output.get("final_plan") is not None:
                final_plan = output["final_plan"]

    if errors:
        print("\nWarnings (non-fatal):")
        for err in errors:
            print(f"  ⚠  {err}")

    if final_plan is None:
        print("\nNo trip plan was produced. Check warnings above.", file=sys.stderr)
        raise SystemExit(1)

    print_trip_plan(final_plan, request)


def main() -> None:
    request = build_request_from_args()
    asyncio.run(run_planner(request))


if __name__ == "__main__":
    main()

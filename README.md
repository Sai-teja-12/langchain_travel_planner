# langchain-travel-planner

Multi-agent travel planner built with **LangChain**, **LangGraph**, and **Gemini**. Five specialist agents research a destination, search flights and hotels, build a day-by-day itinerary, and calculate a budget — orchestrated in parallel by LangGraph.

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env
```

Edit `.env` and set at least:

```
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

Optional keys ground agents in live data (without them, Gemini falls back to built-in knowledge):

```
TAVILY_API_KEY=...
GOOGLE_MAPS_API_KEY=...
SERPAPI_API_KEY=...
```

## Usage

Interactive prompts:

```bash
uv run travel-planner
```

Or pass args:

```bash
uv run travel-planner \
  --origin BLR \
  --destination FCO \
  --departure-date 2026-09-10 \
  --return-date 2026-09-17 \
  --travelers 2 \
  --budget 3000 \
  --preferences "food and museums"
```

Progress ticks print as each graph node finishes (parallel agents may complete in any order), then the full trip plan is pretty-printed. A sample run is saved in [examples/sample_run_blr_fco.md](examples/sample_run_blr_fco.md).


## Architecture

```mermaid
flowchart TD
    User["User enters origin, destination,\ndates, travelers"] --> CLI["CLI builds TravelRequest"]
    CLI --> START(["START — state.request set"])

    START --> destination_research["destination_research\nreads request.origin/destination/dates\ntool: Tavily web_search — visas, weather, tips"]
    START --> flight_search["flight_search\nreads origin → destination, dates, travelers\ntools: SerpAPI + Tavily web_search — flight options"]
    START --> hotel_search["hotel_search\nreads destination, dates, travelers\ntools: Places + Tavily web_search — hotels"]

    destination_research --> itinerary_planner["itinerary_planner\nuses destination research + dates\ntools: Places + Tavily web_search — day-by-day plan"]
    flight_search --> itinerary_planner
    hotel_search --> itinerary_planner

    itinerary_planner --> budget_calculator["budget_calculator\nsums flights + hotels + activities\nx travelers — minimal tools"]
    budget_calculator --> assemble["assemble\n2 Gemini calls: trip summary + 5 tips"]
    assemble --> END_NODE(["END — print TripPlan"])
```

| Node                   | Role                              |
| ---------------------- | --------------------------------- |
| `destination_research` | Visa, weather, tips (Tavily)      |
| `flight_search`        | Flight options (SerpAPI + Tavily) |
| `hotel_search`         | Hotels (Google Places + Tavily)   |
| `itinerary_planner`    | Day-by-day plan                   |
| `budget_calculator`    | Cost breakdown                    |
| `assemble`             | Summary + travel tips             |

There is no budget feedback loop: the graph always proceeds from `budget_calculator` → `assemble` → END.

See [plan.md](plan.md) for the full as-built architecture, agent temps / max iterations, and phase checklist.

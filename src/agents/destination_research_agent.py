import os

from langchain_core.messages import HumanMessage, SystemMessage

from src.config.model_provider import create_model
from src.models.schemas import TravelRequest
from src.tools.web_search import web_search
from src.utils.agent_loop import run_agent_loop

SYSTEM_PROMPT = """You are a destination research specialist. Use web_search to collect:
1. Weather and best time to visit
2. Visa and entry requirements (for travelers from the origin country)
3. Local currency, tipping customs, safety
4. Top neighbourhoods and price ranges
5. Major events during the travel dates
6. Practical tips (transport, SIM cards, power plugs)

Compile a concise markdown summary (300-500 words).
If the search tool fails, use your own knowledge — do not refuse to answer.
"""


async def run_destination_research_agent(request: TravelRequest) -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = create_model(temperature=0.2, provider=provider)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Research: {request.destination}\n"
                f"Travelling from: {request.origin}\n"
                f"Dates: {request.departure_date} to {request.return_date}\n"
                f"Travelers: {request.travelers}\n"
                f"Preferences: {request.preferences or 'none'}"
            )
        ),
    ]
    return await run_agent_loop(
        model, [web_search], messages, max_iter=5, agent_name="destination-research"
    )

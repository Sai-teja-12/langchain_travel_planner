"""LangSmith tracing helpers.

LangChain/LangGraph auto-instrument every model, tool, and graph-node run when
LANGSMITH_TRACING=true. These helpers add the structure that makes those traces
usable for triage:

- a human-readable root run name per trip request (instead of "LangGraph")
- searchable tags and metadata (route, dates, travelers, provider)
- a pre-generated run_id so we can print a direct deep link to the trace
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.models.schemas import TravelRequest


def tracing_enabled() -> bool:
    return os.getenv("LANGSMITH_TRACING", "").lower() in ("true", "1")


def build_root_config(request: TravelRequest) -> Dict[str, Any]:
    """RunnableConfig for the root graph invocation.

    run_name → what shows in the LangSmith runs table (unique per invocation)
    run_id   → known UUID so we can link to the trace after the run
    tags     → coarse filters (product area, route, environment)
    metadata → fine-grained key/values, searchable in the LangSmith UI
    """
    run_id = uuid.uuid4()
    route = f"{request.origin}->{request.destination}"
    started_at = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    short_id = str(run_id)[:8]
    # Route + UTC timestamp + short id so repeated same-route runs are
    # distinguishable. Dates/travelers live in metadata (searchable in UI).
    run_name = f"trip-plan {route} @{started_at} {short_id}"
    return {
        "run_name": run_name,
        "run_id": run_id,
        "tags": [
            "travel-planner",
            f"route:{route}",
            f"env:{os.getenv('APP_ENV', 'dev')}",
        ],
        "metadata": {
            "origin": request.origin,
            "destination": request.destination,
            "departure_date": request.departure_date,
            "return_date": request.return_date,
            "travelers": request.travelers,
            "budget": request.budget,
            "preferences": request.preferences,
            "llm_provider": os.getenv("LLM_PROVIDER", "gemini"),
            "model": os.getenv("GEMINI_MODEL", "unknown"),
            "started_at_utc": started_at,
            "run_id_short": short_id,
        },
    }


def agent_config(agent_name: str, step: str, **metadata: Any) -> Dict[str, Any]:
    """Per-call config so LLM/tool runs are named and filterable by agent."""
    return {
        "run_name": f"{agent_name}:{step}",
        "tags": [f"agent:{agent_name}"],
        "metadata": metadata,
    }


def get_trace_url(run_id: uuid.UUID, retries: int = 5, delay: float = 1.0) -> Optional[str]:
    """Best-effort deep link to the trace in the LangSmith UI.

    Trace ingestion is asynchronous, so flush pending spans first and retry
    the lookup a few times. Returns None if tracing is off or lookup fails.
    """
    if not tracing_enabled():
        return None
    try:
        from langchain_core.tracers.langchain import wait_for_all_tracers
        from langsmith import Client

        wait_for_all_tracers()
        client = Client()
        for attempt in range(retries):
            try:
                return client.read_run(run_id).url
            except Exception:
                if attempt == retries - 1:
                    raise
                time.sleep(delay)
    except Exception:
        return None
    return None

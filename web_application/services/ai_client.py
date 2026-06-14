from __future__ import annotations

import os
import sys
from pathlib import Path

from config import API_BASE_URL
from cursor_sdk import Agent, AgentOptions, CloudAgentOptions, CursorAgentError, LocalAgentOptions
from cursor_sdk import StdioMcpServerConfig

from services.fleet_tools import api_base_url

MODEL = "composer-2.5"

SCOPE_REFUSAL = (
    "Solo puedo ayudarte con preguntas sobre el sistema **Car Tracking**: vehículos, "
    "viajes, pings de ubicación, zonas de estacionamiento, tramos de carretera y "
    "estadísticas de la flota.\n\n"
    "Ejemplos: «¿cuántos vehículos hay?», «¿dónde está el vehículo 3?», "
    "«muéstrame los viajes de hoy»."
)

FLEET_KEYWORDS = (
    "vehicle", "vehículo", "vehiculo", "vehículos", "vehiculos", "vehic",
    "trip", "viaje", "viajes", "trips",
    "ping", "pings", "location", "ubicación", "ubicacion", "ubicaciones",
    "parking", "estacionamiento", "estacionamientos",
    "road", "carretera", "segment", "segmento", "tramo", "tramos", "road segment",
    "breadcrumb", "breadcrumbs", "ruta", "rutas",
    "plate", "matricula", "matrícula", "placa", "placas",
    "fleet", "flota", "tracking", "seguimiento", "car-track", "cartrack",
    "conductor", "flota", "gps", "mapa", "estadística", "estadistica", "stats",
)

SCOPE_RULES = """
STRICT SCOPE — you must follow these rules without exception:
- You ONLY answer questions about this car tracking fleet project: vehicles, trips, location pings, parking areas, road segments, breadcrumbs, and fleet statistics.
- You MUST refuse any question unrelated to this project (general knowledge, animals, history, coding help, trivia, etc.).
- When refusing, reply briefly in the user's language. Do NOT answer the off-topic question at all. Suggest 1–2 example fleet questions they can ask instead.
- Do NOT use external knowledge to answer non-fleet topics, even briefly.
- For fleet questions, always fetch real data with the available tools before answering."""

LOCAL_SYSTEM_PROMPT = """You are a car tracking fleet analyst assistant for the Car Tracking project ONLY.
{scope_rules}

Always fetch real data using the fleet-api MCP tools before answering fleet-related questions. When presenting results:
- Refer to vehicles by plate number when possible
- Use clear, concise language
- Summarize large datasets rather than dumping raw JSON
- Timestamps should be interpreted as ISO 8601 without timezone (e.g. 2026-03-14T15:30:00)
- If paginated data is returned (items, limit, offset, count), use the full response to give accurate counts and summaries
- If a tool returns an error, explain it to the user in plain language

The car tracking REST API base URL is {api_base_url}. The MCP tools call this API directly."""

CLOUD_SYSTEM_PROMPT = """You are a car tracking fleet analyst assistant for the Car Tracking project ONLY.
{scope_rules}

The car tracking REST API base URL is: {api_base_url}

Before answering fleet-related questions, fetch real data from the API using shell/curl or web fetch. Available GET endpoints:
- /vehicles?limit=50
- /vehicles/{{vehicle_id}}/current-location
- /vehicles/{{vehicle_id}}/trips?limit=50&offset=0
- /vehicles/{{vehicle_id}}/pings?limit=100&from_ts=&to_ts=
- /vehicles/{{vehicle_id}}/breadcrumb?from_ts=&to_ts=
- /location-pings/latest?bbox=minLon,minLat,maxLon,maxLat
- /stats/pings-per-day?from_ts=&to_ts=
- /trips?limit=50&offset=0
- /parking-areas/map?limit=300&bbox=

When presenting fleet results:
- Refer to vehicles by plate number when possible
- Use clear, concise language
- Summarize large datasets rather than dumping raw JSON
- Timestamps must be ISO 8601 without timezone (e.g. 2026-03-14T15:30:00)
- If paginated data is returned (items, limit, offset, count), use the full response for accurate counts
- If an API call fails, explain the error in plain language"""


def _is_in_scope(message: str) -> bool:
    text = message.lower()
    return any(keyword in text for keyword in FLEET_KEYWORDS)


def _uses_internal_api() -> bool:
    base = os.getenv("API_BASE_URL", API_BASE_URL)
    return any(token in base for token in ("api:8000", "localhost", "127.0.0.1"))


def _is_local_runtime() -> bool:
    runtime = os.getenv("CURSOR_AGENT_RUNTIME", "").strip().lower()
    if runtime == "local":
        return True
    if runtime == "cloud":
        return False
    return _uses_internal_api()


def _mcp_server_path() -> str:
    return str(Path(__file__).resolve().parent / "fleet_mcp_server.py")


def _build_mcp_servers() -> dict[str, StdioMcpServerConfig]:
    return {
        "fleet-api": StdioMcpServerConfig(
            command=sys.executable,
            args=[_mcp_server_path()],
            env={"API_BASE_URL": os.getenv("API_BASE_URL", API_BASE_URL)},
        )
    }


def _build_agent_options(api_key: str) -> AgentOptions:
    mcp_servers = _build_mcp_servers()

    if _is_local_runtime():
        project_root = str(Path(__file__).resolve().parents[1])
        return AgentOptions(
            api_key=api_key,
            model=MODEL,
            local=LocalAgentOptions(cwd=project_root),
            mcp_servers=mcp_servers,
            name="Car Tracking Fleet Analyst",
        )

    public_url = os.getenv("PUBLIC_API_BASE_URL", api_base_url())
    return AgentOptions(
        api_key=api_key,
        model=MODEL,
        cloud=CloudAgentOptions(),
        mcp_servers={
            "fleet-api": StdioMcpServerConfig(
                command=sys.executable,
                args=[_mcp_server_path()],
                env={"API_BASE_URL": public_url},
            )
        },
        name="Car Tracking Fleet Analyst",
    )


def _system_prompt() -> str:
    template = LOCAL_SYSTEM_PROMPT if _is_local_runtime() else CLOUD_SYSTEM_PROMPT
    return template.format(api_base_url=api_base_url(), scope_rules=SCOPE_RULES)


def _build_user_prompt(user_message: str, system: str, agent_id: str | None) -> str:
    scope_note = (
        "Reminder: only answer if this question is about the car tracking fleet project; "
        "otherwise refuse without answering the off-topic question."
    )
    if agent_id:
        return f"{scope_note}\n\nUser question: {user_message}"
    return f"{system}\n\nUser question: {user_message}"


def run_assistant(user_message: str, agent_id: str | None = None) -> tuple[str, str]:
    api_key = os.getenv("CURSOR_API_KEY", "").strip()
    if not api_key:
        raise ValueError("CURSOR_API_KEY environment variable is not set")

    if not _is_in_scope(user_message):
        return SCOPE_REFUSAL, agent_id

    options = _build_agent_options(api_key)
    system = _system_prompt()

    try:
        if agent_id:
            agent_ctx = Agent.resume(agent_id, options)
        else:
            agent_ctx = Agent.create(options)

        prompt = _build_user_prompt(user_message, system, agent_id)

        with agent_ctx as agent:
            run = agent.send(prompt)
            result = run.wait()
            if result.status == "error":
                raise RuntimeError(f"Agent run failed (run id: {result.id})")
            text = run.text().strip()
            if not text:
                text = "I couldn't generate a response."
            return text, agent.agent_id
    except CursorAgentError as exc:
        raise RuntimeError(f"Cursor agent error: {exc.message}") from exc

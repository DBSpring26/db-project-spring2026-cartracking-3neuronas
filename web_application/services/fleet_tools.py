from __future__ import annotations

import json
import os
from typing import Any, Optional

import requests

from config import API_BASE_URL
from services.api_client import APIClient


def api_base_url() -> str:
    public = os.getenv("PUBLIC_API_BASE_URL", "").strip()
    if public:
        return public.rstrip("/")
    return API_BASE_URL.rstrip("/")


def _direct_get(path: str, params: Optional[dict[str, Any]] = None) -> Any:
    if not path.startswith("/"):
        path = "/" + path
    url = f"{api_base_url()}{path}"
    try:
        response = requests.get(url, params=params or {}, timeout=15)
        if response.status_code == 204:
            return {"message": "No current location available for this vehicle"}
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        try:
            data = response.json()
            msg = data.get("error") or data.get("detail") or str(data)
        except Exception:
            msg = response.text or f"HTTP {response.status_code}"
        return {"error": msg}
    except requests.RequestException as exc:
        return {"error": str(exc)}


def format_tool_result(result: Any) -> str:
    if result is None:
        return json.dumps({"error": "API request failed or returned no data"})
    return json.dumps(result)


def execute_tool(name: str, tool_input: dict[str, Any]) -> str:
    client = APIClient()
    try:
        if name == "get_vehicles":
            limit = tool_input.get("limit", 50)
            return format_tool_result(client.get_vehicles(limit=limit))

        if name == "get_vehicle_location":
            vehicle_id = tool_input["vehicle_id"]
            method = getattr(client, "get_vehicle_location", None)
            if callable(method):
                return format_tool_result(method(vehicle_id))
            return format_tool_result(_direct_get(f"/vehicles/{vehicle_id}/current-location"))

        if name == "get_vehicle_trips":
            vehicle_id = tool_input["vehicle_id"]
            kwargs: dict[str, Any] = {}
            if "limit" in tool_input:
                kwargs["limit"] = tool_input["limit"]
            if "offset" in tool_input:
                kwargs["offset"] = tool_input["offset"]
            method = getattr(client, "get_vehicle_trips", None)
            if callable(method):
                return format_tool_result(method(vehicle_id=vehicle_id, **kwargs))
            return format_tool_result(_direct_get(f"/vehicles/{vehicle_id}/trips", kwargs))

        if name == "get_vehicle_pings":
            vehicle_id = tool_input["vehicle_id"]
            params: dict[str, Any] = {}
            if "from_ts" in tool_input:
                params["from_ts"] = tool_input["from_ts"]
            if "to_ts" in tool_input:
                params["to_ts"] = tool_input["to_ts"]
            if "limit" in tool_input:
                params["limit"] = tool_input["limit"]
            method = getattr(client, "get_vehicle_pings", None)
            if callable(method):
                return format_tool_result(method(vehicle_id=vehicle_id, **params))
            return format_tool_result(_direct_get(f"/vehicles/{vehicle_id}/pings", params))

        if name == "get_breadcrumb":
            return format_tool_result(
                client.get_breadcrumb(
                    vehicle_id=tool_input["vehicle_id"],
                    from_ts=tool_input["from_ts"],
                    to_ts=tool_input["to_ts"],
                )
            )

        if name == "get_latest_pings":
            bbox = tool_input.get("bbox")
            return format_tool_result(client.get_latest_pings(bbox=bbox))

        if name == "get_pings_per_day":
            return format_tool_result(
                client.get_pings_per_day(
                    from_ts=tool_input.get("from_ts"),
                    to_ts=tool_input.get("to_ts"),
                )
            )

        if name == "get_trips":
            kwargs = {}
            if "limit" in tool_input:
                kwargs["limit"] = tool_input["limit"]
            if "offset" in tool_input:
                kwargs["offset"] = tool_input["offset"]
            method = getattr(client, "get_trips", None)
            if callable(method):
                return format_tool_result(method(**kwargs))
            return format_tool_result(_direct_get("/trips", kwargs))

        if name == "get_parking_areas":
            kwargs = {}
            if "limit" in tool_input:
                kwargs["limit"] = tool_input["limit"]
            if "bbox" in tool_input:
                kwargs["bbox"] = tool_input["bbox"]
            return format_tool_result(client.get_parking_areas(**kwargs))

        return json.dumps({"error": f"Unknown tool: {name}"})
    except KeyError as exc:
        return json.dumps({"error": f"Missing required parameter: {exc}"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})

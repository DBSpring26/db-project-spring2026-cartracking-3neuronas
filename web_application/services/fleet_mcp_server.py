"""Stdio MCP server exposing fleet REST API tools for local Cursor agents."""

from __future__ import annotations

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from services.fleet_tools import execute_tool

mcp = FastMCP("car-tracking-fleet")


def _parse_result(raw: str) -> str:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(data, dict) and "error" in data:
        return f"API error: {data['error']}"
    return raw


@mcp.tool()
def get_vehicles(limit: int = 50) -> str:
    """Get list of all vehicles with plate numbers, make, model, year and status."""
    return _parse_result(execute_tool("get_vehicles", {"limit": limit}))


@mcp.tool()
def get_vehicle_location(vehicle_id: int) -> str:
    """Get the current/latest location of a specific vehicle."""
    return _parse_result(execute_tool("get_vehicle_location", {"vehicle_id": vehicle_id}))


@mcp.tool()
def get_vehicle_trips(
    vehicle_id: int,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> str:
    """Get trips for a specific vehicle."""
    payload: dict = {"vehicle_id": vehicle_id}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return _parse_result(execute_tool("get_vehicle_trips", payload))


@mcp.tool()
def get_vehicle_pings(
    vehicle_id: int,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
    limit: Optional[int] = None,
) -> str:
    """Get location pings for a vehicle, optionally filtered by time range."""
    payload: dict = {"vehicle_id": vehicle_id}
    if from_ts:
        payload["from_ts"] = from_ts
    if to_ts:
        payload["to_ts"] = to_ts
    if limit is not None:
        payload["limit"] = limit
    return _parse_result(execute_tool("get_vehicle_pings", payload))


@mcp.tool()
def get_breadcrumb(vehicle_id: int, from_ts: str, to_ts: str) -> str:
    """Get the full route of a vehicle between two timestamps."""
    return _parse_result(
        execute_tool(
            "get_breadcrumb",
            {"vehicle_id": vehicle_id, "from_ts": from_ts, "to_ts": to_ts},
        )
    )


@mcp.tool()
def get_latest_pings(bbox: Optional[str] = None) -> str:
    """Get the most recent location ping for every active vehicle."""
    payload = {}
    if bbox:
        payload["bbox"] = bbox
    return _parse_result(execute_tool("get_latest_pings", payload))


@mcp.tool()
def get_pings_per_day(from_ts: Optional[str] = None, to_ts: Optional[str] = None) -> str:
    """Get a count of location pings grouped by day."""
    payload = {}
    if from_ts:
        payload["from_ts"] = from_ts
    if to_ts:
        payload["to_ts"] = to_ts
    return _parse_result(execute_tool("get_pings_per_day", payload))


@mcp.tool()
def get_trips(limit: Optional[int] = None, offset: Optional[int] = None) -> str:
    """Get all trips across all vehicles."""
    payload = {}
    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    return _parse_result(execute_tool("get_trips", payload))


@mcp.tool()
def get_parking_areas(limit: Optional[int] = None, bbox: Optional[str] = None) -> str:
    """Get parking areas with name, capacity and geometry."""
    payload = {}
    if limit is not None:
        payload["limit"] = limit
    if bbox:
        payload["bbox"] = bbox
    return _parse_result(execute_tool("get_parking_areas", payload))


if __name__ == "__main__":
    mcp.run()

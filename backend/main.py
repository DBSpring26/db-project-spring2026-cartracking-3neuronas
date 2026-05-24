"""
Car Tracking API — FastAPI entry (CIIC 4060 / ICOM 5016, Spring 2026, UPRM).

Thin endpoints: instantiate handlers, delegate business logic and HTTPException to handler layer.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from .handler.location_ping_handler import LocationPingHandler
from .handler.parking_area_handler import ParkingAreaHandler
from .handler.road_segment_handler import RoadSegmentHandler
from .handler.stats_handler import StatsHandler
from .handler.trip_handler import TripHandler
from .handler.user_handler import UserHandler
from .handler.vehicle_handler import VehicleHandler

# ---------------------------------------------------------------------------
# Pydantic request models (GeoJSON SRID 4326; coordinates [lon, lat])
# ---------------------------------------------------------------------------


class GeoJSONPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Point"]
    coordinates: list[float]


class GeoJSONLineString(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["LineString"]
    coordinates: list[list[float]]


class GeoJSONPolygon(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]


class VehicleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type_id: int
    vehicle_status_id: int
    plate_number: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: int = Field(..., ge=1950, le=2100)


class VehicleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type_id: Optional[int] = None
    vehicle_status_id: Optional[int] = None
    plate_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1950, le=2100)


class RoadSegmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    speed_limit_kph: Optional[int] = None
    is_oneway: Optional[bool] = None
    direction: Optional[str] = None
    geom: GeoJSONLineString


class RoadSegmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    speed_limit_kph: Optional[int] = None
    is_oneway: Optional[bool] = None
    direction: Optional[str] = None
    geom: Optional[GeoJSONLineString] = None


class ParkingAreaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    capacity: Optional[int] = None
    geom: GeoJSONPolygon


class ParkingAreaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    capacity: Optional[int] = None
    geom: Optional[GeoJSONPolygon] = None


class LocationPingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: int
    ts: str
    geom: GeoJSONPoint
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None


class LocationPingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: Optional[int] = None
    ts: Optional[str] = None
    geom: Optional[GeoJSONPoint] = None
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None


class TripCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: int
    start_ts: str
    end_ts: str
    start_geom: Optional[GeoJSONPoint] = None
    end_geom: Optional[GeoJSONPoint] = None
    distance_km: Optional[float] = None


class TripUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: Optional[int] = None
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    start_geom: Optional[GeoJSONPoint] = None
    end_geom: Optional[GeoJSONPoint] = None
    distance_km: Optional[float] = None


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    password: str


# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    _create_app_user_table()
    yield


def _create_app_user_table():
    from .config.dbconfig import PG_DB_CONFIG
    import psycopg2

    conn = psycopg2.connect(**PG_DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_user (
                    user_id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
        conn.commit()
    finally:
        conn.close()


app = FastAPI(title="Car Tracking API", version="1.0.0", lifespan=lifespan)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 5.1 Vehicles — /api/v1/vehicles
# ---------------------------------------------------------------------------


@app.post("/api/v1/vehicles", status_code=201)
async def create_vehicle(new_vehicle: VehicleCreate):
    return VehicleHandler().create_vehicle(new_vehicle)


@app.get("/api/v1/vehicles")
async def get_vehicles(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    plate_number: Optional[str] = None,
):
    return VehicleHandler().get_all_vehicles(limit, offset, status, plate_number)


@app.get("/api/v1/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: int):
    return VehicleHandler().get_vehicle_by_id(vehicle_id)


@app.put("/api/v1/vehicles/{vehicle_id}")
async def update_vehicle(vehicle_id: int, body: VehicleUpdate):
    return VehicleHandler().update_vehicle(vehicle_id, body)


@app.delete("/api/v1/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int):
    return VehicleHandler().delete_vehicle(vehicle_id)


@app.get("/api/v1/vehicles/{vehicle_id}/current-location")
async def get_vehicle_current_location(vehicle_id: int):
    result = VehicleHandler().get_vehicle_current_location(vehicle_id)
    if result is None:
        return Response(status_code=204)
    return result


@app.get("/api/v1/vehicles/{vehicle_id}/pings")
async def get_vehicle_pings(
    vehicle_id: int,
    limit: int = 100,
    offset: int = 0,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
):
    return VehicleHandler().get_vehicle_pings(vehicle_id, limit, offset, from_ts, to_ts)


@app.get("/api/v1/vehicles/{vehicle_id}/trips")
async def get_vehicle_trips(
    vehicle_id: int,
    limit: int = 50,
    offset: int = 0,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
):
    return VehicleHandler().get_vehicle_trips(vehicle_id, limit, offset, from_ts, to_ts)


# ---------------------------------------------------------------------------
# 5.2 Road segments — /api/v1/road-segments
# ---------------------------------------------------------------------------


@app.post("/api/v1/road-segments", status_code=201)
async def create_road_segment(new_segment: RoadSegmentCreate):
    return RoadSegmentHandler().create_road_segment(new_segment)


@app.get("/api/v1/road-segments")
async def get_road_segments(
    limit: int = 20,
    offset: int = 0,
    name: Optional[str] = None,
    min_speed: Optional[int] = None,
    max_speed: Optional[int] = None,
    bbox: Optional[str] = None,
):
    return RoadSegmentHandler().get_all_road_segments(
        limit, offset, name, min_speed, max_speed, bbox
    )


@app.get("/api/v1/road-segments/map")
async def get_road_segments_map(
    limit: int = 5000,
    offset: int = 0,
    name: Optional[str] = None,
    min_speed: Optional[int] = None,
    max_speed: Optional[int] = None,
    bbox: Optional[str] = None,
):
    return RoadSegmentHandler().get_road_segments_map(limit, offset, name, min_speed, max_speed, bbox)


@app.get("/api/v1/road-segments/{road_id}")
async def get_road_segment(road_id: int):
    return RoadSegmentHandler().get_road_segment_by_id(road_id)


@app.put("/api/v1/road-segments/{road_id}")
async def update_road_segment(road_id: int, body: RoadSegmentUpdate):
    return RoadSegmentHandler().update_road_segment(road_id, body)


@app.delete("/api/v1/road-segments/{road_id}")
async def delete_road_segment(road_id: int):
    return RoadSegmentHandler().delete_road_segment(road_id)


# ---------------------------------------------------------------------------
# 5.3 Parking areas — /api/v1/parking-areas
# ---------------------------------------------------------------------------


@app.post("/api/v1/parking-areas", status_code=201)
async def create_parking_area(new_area: ParkingAreaCreate):
    return ParkingAreaHandler().create_parking_area(new_area)


@app.get("/api/v1/parking-areas")
async def get_parking_areas(
    limit: int = 20,
    offset: int = 0,
    name: Optional[str] = None,
    bbox: Optional[str] = None,
):
    return ParkingAreaHandler().get_all_parking_areas(limit, offset, name, bbox)


@app.get("/api/v1/parking-areas/map")
async def get_parking_areas_map(
    limit: int = 300,
    offset: int = 0,
    name: Optional[str] = None,
    bbox: Optional[str] = None,
):
    return ParkingAreaHandler().get_parking_areas_map(limit, offset, name, bbox)


@app.get("/api/v1/parking-areas/{parking_area_id}")
async def get_parking_area(parking_area_id: int):
    return ParkingAreaHandler().get_parking_area_by_id(parking_area_id)


@app.put("/api/v1/parking-areas/{parking_area_id}")
async def update_parking_area(parking_area_id: int, body: ParkingAreaUpdate):
    return ParkingAreaHandler().update_parking_area(parking_area_id, body)


@app.delete("/api/v1/parking-areas/{parking_area_id}")
async def delete_parking_area(parking_area_id: int):
    return ParkingAreaHandler().delete_parking_area(parking_area_id)


# ---------------------------------------------------------------------------
# 5.4 Location pings — /api/v1/location-pings
# ---------------------------------------------------------------------------


@app.post("/api/v1/location-pings", status_code=201)
async def create_location_ping(new_ping: LocationPingCreate):
    return LocationPingHandler().create_location_ping(new_ping)


@app.get("/api/v1/location-pings")
async def get_location_pings(
    limit: int = 100,
    offset: int = 0,
    vehicle_id: Optional[int] = None,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
    bbox: Optional[str] = None,
):
    return LocationPingHandler().get_all_location_pings(
        limit, offset, vehicle_id, from_ts, to_ts, bbox
    )


# Latest pings
@app.get("/api/v1/location-pings/latest")
async def get_latest_pings(bbox: Optional[str] = None):
    return LocationPingHandler().get_latest_pings(bbox)


@app.get("/api/v1/location-pings/{ping_id}")
async def get_location_ping(ping_id: int):
    return LocationPingHandler().get_location_ping_by_id(ping_id)


@app.put("/api/v1/location-pings/{ping_id}")
async def update_location_ping(ping_id: int, body: LocationPingUpdate):
    return LocationPingHandler().update_location_ping(ping_id, body)


@app.delete("/api/v1/location-pings/{ping_id}")
async def delete_location_ping(ping_id: int):
    return LocationPingHandler().delete_location_ping(ping_id)


# ---------------------------------------------------------------------------
# 5.5 Trips — /api/v1/trips
# ---------------------------------------------------------------------------


@app.post("/api/v1/trips", status_code=201)
async def create_trip(new_trip: TripCreate):
    return TripHandler().create_trip(new_trip)


@app.get("/api/v1/trips")
async def get_trips(
    limit: int = 50,
    offset: int = 0,
    vehicle_id: Optional[int] = None,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
):
    return TripHandler().get_all_trips(limit, offset, vehicle_id, from_ts, to_ts)


@app.get("/api/v1/trips/{trip_id}")
async def get_trip(trip_id: int):
    return TripHandler().get_trip_by_id(trip_id)


@app.put("/api/v1/trips/{trip_id}")
async def update_trip(trip_id: int, body: TripUpdate):
    return TripHandler().update_trip(trip_id, body)


@app.delete("/api/v1/trips/{trip_id}")
async def delete_trip(trip_id: int):
    return TripHandler().delete_trip(trip_id)


# Users
@app.post("/api/v1/users/signup", status_code=201)
async def signup(body: UserCreate):
    return UserHandler().signup(body)


@app.post("/api/v1/users/login")
async def login(body: UserLogin):
    return UserHandler().login(body)


# Breadcrumb
@app.get("/api/v1/vehicles/{vehicle_id}/breadcrumb")
async def get_breadcrumb(vehicle_id: int, from_ts: str, to_ts: str):
    return VehicleHandler().get_breadcrumb(vehicle_id, from_ts, to_ts)


# Stats
@app.get("/api/v1/stats/pings-per-day")
async def get_pings_per_day(
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
):
    return StatsHandler().get_pings_per_day(from_ts, to_ts)

# Car Tracking API — Phase II
**ICOM 5016 – Spring 2026**  
**Team: 3 Neuronas**

## Team Members & Contributions

| Member | Role | Responsibility |
|--------|------|---------------|
| Jorge Burgos | Routing Layer | `main.py` `load.py`
| Roberto Galarza | DAO Layer | `dao/` `collection`
| Christian Perez | Handler Layer | `handler/`

## Database Credentials (Render)
- **Host:** `dpg-d6rbqdkr85hc73a2ovng-a.virginia-postgres.render.com`
- **Database:** `dbproject_y601`
- **User:** `neurona1`
- **Password:** `YGS3uNZ247ukda0t9RLZ4AGrKYyjPOeq`
- **Port:** `5432`

## API Base URL
https://db-project-spring2026-cartracking-0cax.onrender.com

## API Documentation
Interactive Swagger docs available at:
https://db-project-spring2026-cartracking-0cax.onrender.com/docs

## Base Path
All endpoints are prefixed with `/api/v1`

## Endpoints Summary

### Vehicles
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/vehicles` | Create a vehicle |
| GET | `/api/v1/vehicles` | List vehicles (paginated, filterable) |
| GET | `/api/v1/vehicles/{vehicle_id}` | Get vehicle by ID |
| PUT | `/api/v1/vehicles/{vehicle_id}` | Update vehicle (partial or full) |
| DELETE | `/api/v1/vehicles/{vehicle_id}` | Delete vehicle |
| GET | `/api/v1/vehicles/{vehicle_id}/current-location` | Get most recent location |
| GET | `/api/v1/vehicles/{vehicle_id}/pings` | Get pings for a vehicle |
| GET | `/api/v1/vehicles/{vehicle_id}/trips` | Get trips for a vehicle |

### Road Segments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/road-segments` | Create a road segment |
| GET | `/api/v1/road-segments` | List road segments (filterable by name, speed, bbox) |
| GET | `/api/v1/road-segments/{road_id}` | Get road segment by ID |
| PUT | `/api/v1/road-segments/{road_id}` | Update road segment |
| DELETE | `/api/v1/road-segments/{road_id}` | Delete road segment |

### Parking Areas
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/parking-areas` | Create a parking area |
| GET | `/api/v1/parking-areas` | List parking areas (filterable by name, bbox) |
| GET | `/api/v1/parking-areas/{parking_area_id}` | Get parking area by ID |
| PUT | `/api/v1/parking-areas/{parking_area_id}` | Update parking area |
| DELETE | `/api/v1/parking-areas/{parking_area_id}` | Delete parking area |

### Location Pings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/location-pings` | Create a location ping |
| GET | `/api/v1/location-pings` | List pings (filterable by vehicle, time range, bbox) |
| GET | `/api/v1/location-pings/{ping_id}` | Get ping by ID |
| PUT | `/api/v1/location-pings/{ping_id}` | Update ping |
| DELETE | `/api/v1/location-pings/{ping_id}` | Delete ping |

### Trips
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/trips` | Create a trip |
| GET | `/api/v1/trips` | List trips (filterable by vehicle, time range) |
| GET | `/api/v1/trips/{trip_id}` | Get trip by ID |
| PUT | `/api/v1/trips/{trip_id}` | Update trip |
| DELETE | `/api/v1/trips/{trip_id}` | Delete trip |

## Technical Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL 17 + PostGIS
- **Driver:** psycopg2
- **Hosting:** Render
- **Architecture:** Handler/DAO pattern (MVC)
- **Geometry:** GeoJSON (Point, LineString, Polygon) — SRID 4326
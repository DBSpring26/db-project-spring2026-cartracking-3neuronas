# Car Tracking API — Phase III
**ICOM 5016 – Spring 2026**  
**Team: 3 Neuronas**

## Team Members & Contributions

| Member | Role | Responsibility |
|--------|------|---------------|
| Jorge Burgos | Pages Layer | `web_application/pages/` |
| Roberto Galarza | Backend Layer | `backend/` |
| Christian Perez | Services & Utils Layer | `web_application/services/`, `web_application/utils/` |

## Database Credentials (Render)
- **Host:** `dpg-d6rbqdkr85hc73a2ovng-a.virginia-postgres.render.com`
- **Database:** `dbproject_y601`
- **User:** `neurona1`
- **Password:** `YGS3uNZ247ukda0t9RLZ4AGrKYyjPOeq`
- **Port:** `5432`

## API Base URL
https://db-project-spring2026-cartracking-0cax.onrender.com

## Web Application URL
https://db-project-spring2026-cartracking-hjmt.onrender.com/

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
| GET | `/api/v1/vehicles/{vehicle_id}/breadcrumb` | Get vehicle route (breadcrumb) for a time range |

### Road Segments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/road-segments` | Create a road segment |
| GET | `/api/v1/road-segments` | List road segments (filterable by name, speed, bbox) |
| GET | `/api/v1/road-segments/map` | List road segments for map display (GeoJSON, filterable) |
| GET | `/api/v1/road-segments/{road_id}` | Get road segment by ID |
| PUT | `/api/v1/road-segments/{road_id}` | Update road segment |
| DELETE | `/api/v1/road-segments/{road_id}` | Delete road segment |

### Parking Areas
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/parking-areas` | Create a parking area |
| GET | `/api/v1/parking-areas` | List parking areas (filterable by name, bbox) |
| GET | `/api/v1/parking-areas/map` | List parking areas for map display (GeoJSON, filterable) |
| GET | `/api/v1/parking-areas/{parking_area_id}` | Get parking area by ID |
| PUT | `/api/v1/parking-areas/{parking_area_id}` | Update parking area |
| DELETE | `/api/v1/parking-areas/{parking_area_id}` | Delete parking area |

### Location Pings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/location-pings` | Create a location ping |
| GET | `/api/v1/location-pings` | List pings (filterable by vehicle, time range, bbox) |
| GET | `/api/v1/location-pings/latest` | Get latest ping per vehicle (filterable by bbox) |
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

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/signup` | Register a new user |
| POST | `/api/v1/users/login` | Authenticate user |

### Stats
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stats/pings-per-day` | Get ping count per day (filterable by time range) |

## Technical Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL 17 + PostGIS
- **Driver:** psycopg2
- **Hosting:** Render
- **Architecture:** Handler/DAO pattern (MVC)
- **Geometry:** GeoJSON (Point, LineString, Polygon) — SRID 4326
- **API Docs:** Swagger/OpenAPI (`/docs`)

### Web Application
- **Framework:** Streamlit
- **Maps:** Folium + streamlit-folium
- **Charts:** Plotly
- **HTTP Client:** requests
- **Data:** pandas

### ETL
- **Pipeline:** Python (extract / transform / load)
- **Libraries:** pandas, pyarrow, tqdm

### DevOps
- **Containerization:** Docker + Docker Compose
- **Services:** postgres, api, web
- **Hosting:** Render
- **Python:** 3.11
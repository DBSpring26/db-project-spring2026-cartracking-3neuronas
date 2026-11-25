# Car Tracking API — Phase III
**ICOM 5016 – Spring 2026**  
**Team: 3 Neuronas**

## Team Members & Contributions

### Jorge Burgos — Frontend & Data Visualization
- **Frontend & Data Visualization:** Streamlit pages (Signup, Parking Areas, Road Segments, Vehicle Pings, Breadcrumbs, Dashboards); JSON-to-UI tables; map utilities and bbox tracking.
- **Shared with the team:** ETL pipeline and backend architecture (Handlers and DAOs).
- **Solo, later addition (not part of the original project scope):** the conversational AI Assistant.

### Christian Perez — DevOps & Core Architecture
- DevOps & core architecture (`app.py` / session / API client, Docker, Render deploy), plus shared ETL/backend.

### Roberto Galarza — API Design & QA
- API design & QA (Postman, route testing, endpoint contracts), plus shared ETL/backend.

> The 28-endpoint REST API, FastAPI, and ETL pipeline were built collaboratively by the whole team.

## Environment setup

Copy `.env.example` to `.env` and fill in values. Required for Docker Compose, local runs, ETL (Render), and the AI Assistant (`CURSOR_API_KEY`).

## AI Assistant

In-app chat ( **AI Assistant** page) that answers fleet questions using live API data.

### Features
- Natural-language queries about vehicles, trips, pings, parking areas, road segments, and statistics.
- Answers only Car Tracking project topics; refuses out-of-scope questions.
- Keeps conversation context via the agent (`Agent.resume`) until **Clear conversation** is clicked in the sidebar.

### Configuration (`.env`)
| Variable | Description |
|----------|-------------|
| `CURSOR_API_KEY` | Cursor API key (required to use the assistant) |
| `CURSOR_AGENT_RUNTIME` | `local` (default) or `cloud` |
| `API_BASE_URL` | Internal API URL (Docker/local) |
| `PUBLIC_API_BASE_URL` | Public API URL (Render) for cloud runtime |

In Docker Compose, the `web` service receives `CURSOR_API_KEY` and `CURSOR_AGENT_RUNTIME` from `.env`.

### Architecture
- **`web_application/pages/7_AI_Assistant.py`** — Streamlit chat UI (login required).
- **`web_application/services/ai_client.py`** — Cursor SDK agent orchestration (`composer-2.5`), scope validation, and prompts.
- **`web_application/services/fleet_mcp_server.py`** — Stdio MCP server exposing REST API tools.
- **`web_application/services/fleet_tools.py`** — GET request execution against the API.

**Local runtime:** local agent + MCP `fleet-api` pointing to `API_BASE_URL`.  
**Cloud runtime:** cloud agent + MCP using `PUBLIC_API_BASE_URL`.

## Database Credentials (Render)

Configure production database access via environment variables. Copy `.env.example` to `.env` and set `DB_HOST`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` (used by the ETL pipeline).

- **Host:** see `DB_HOST` in your `.env`
- **Database / User / Password:** see `.env`
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
- **AI Assistant:** Cursor SDK + MCP (`cursor-sdk`, `mcp`)
- **Env:** python-dotenv

### ETL
- **Pipeline:** Python (extract / transform / load)
- **Libraries:** pandas, pyarrow, tqdm

### DevOps
- **Containerization:** Docker + Docker Compose
- **Services:** postgres, api, web
- **Hosting:** Render
- **Python:** 3.11

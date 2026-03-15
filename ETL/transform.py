from __future__ import annotations

EXPECTED_COLUMNS = {
    "fuel_type": ["fuel_type_id", "name"],
    "vehicle_kind": ["vehicle_kind_id", "name"],
    "vehicle_status": ["vehicle_status_id", "name"],
    "vehicle_type": ["id", "vehicle_kind_id", "fuel_type_id", "emissions_rating", "created_at"],
    "vehicle": [
        "vehicle_id",
        "vehicle_type_id",
        "vehicle_status_id",
        "plate_number",
        "make",
        "model",
        "year",
        "created_at",
    ],
    "trip": ["trip_id", "vehicle_id", "start_ts", "end_ts", "start_geom", "end_geom", "distance_km"],
    "parking_area": ["parking_area_id", "name", "capacity", "geom", "created_at"],
    "road_segment": ["road_id", "name", "speed_limit_kph", "geom", "created_at", "is_oneway", "direction"],
    "location_ping": ["ping_id", "vehicle_id", "ts", "geom", "speed_kph", "heading_deg"],
}


def validate_data(data):
    for name, df in data.items():
        if df.empty:
            raise ValueError(f"The dataset '{name}' is empty.")

        expected_columns = EXPECTED_COLUMNS[name]
        actual_columns = list(df.columns)

        if actual_columns != expected_columns:
            raise ValueError(
                f"Column mismatch in '{name}'. Expected {expected_columns}, but found {actual_columns}."
            )

    return data

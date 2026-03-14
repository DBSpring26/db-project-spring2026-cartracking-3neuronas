
import pandas as pd
from pathlib import Path

def extract_all(data_dir):
    data_dir = Path(data_dir)

    return {
        "fuel_type": pd.read_parquet(data_dir / "fuel_type.parquet"),
        "vehicle_kind": pd.read_parquet(data_dir / "vehicle_kind.parquet"),
        "vehicle_status": pd.read_parquet(data_dir / "vehicle_status.parquet"),
        "vehicle_type": pd.read_parquet(data_dir / "vehicle_type.parquet"),
        "vehicle": pd.read_parquet(data_dir / "vehicle.parquet"),
        "trip": pd.read_parquet(data_dir / "trip.parquet"),
        "parking_area": pd.read_parquet(data_dir / "parking_area.parquet"),
        "road_segment": pd.read_parquet(data_dir / "road_segment.parquet"),
        "location_ping": pd.read_parquet(data_dir / "location_ping.parquet"),
    }

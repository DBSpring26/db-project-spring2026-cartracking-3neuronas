from __future__ import annotations

import argparse

from extract import extract_all
from load import load_all
from transform import validate_data


def run(data_dir: str) -> None:
    print("Extracting parquet files...")
    data = extract_all(data_dir)

    print("Validating extracted datasets...")
    validated_data = validate_data(data)

    print("Loading data into PostgreSQL/PostGIS...")
    load_all(validated_data)

    print("ETL completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Car Tracking ETL pipeline.")
    parser.add_argument(
        "--project-data",
        required=True,
        help="Path to the directory that contains the Parquet files.",
    )

    arguments = parser.parse_args()
    run(arguments.project_data)

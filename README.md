# Car Tracking - Phase I (Database + ETL)

This repository contains the ETL pipeline for the Car Tracking Phase I deliverable.
The pipeline reads the provided Parquet datasets and loads them into PostgreSQL 17
with the PostGIS extension enabled.

## Project structure

- `extract.py`: reads all required Parquet files.
- `transform.py`: validates that each dataset matches the required schema.
- `load.py`: creates the database schema and loads all records.
- `pipeline.py`: runs the complete ETL process.
- `dbconfig.py`: database connection settings.
- `docker-compose.yml` and `Dockerfile`: local test environment using PostgreSQL 17 + PostGIS.

## Database credentials

-Hostname: dpg-d6rbqdkr85hc73a2ovng-a.virginia-postgres.render.com

-Port: 5432

-database: dbproject_y601

-username: neurona1

-password: YGS3uNZ247ukda0t9RLZ4AGrKYyjPOeq



You can override them with environment variables:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

## Local setup

Start PostgreSQL/PostGIS:

```bash
docker-compose up -d
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run the ETL pipeline:

```bash
python pipeline.py --project-data ./project_data
```

## Notes

- The relational schema strictly follows the table diagram provided in the project handout.
- All geometries are stored with SRID 4326, as requested in the assignment.
- The ETL process validates the exact column order of each CSV before loading it into the database.
- For this final submission, the production database is deployed on Render, in accordance with the project requirements.

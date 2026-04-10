from __future__ import annotations

from datetime import datetime
from typing import Optional

import psycopg2
from fastapi import HTTPException

from dao.vehicle_dao import VehicleDAO, VehicleCreate, VehicleUpdate


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    if value == "":
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid timestamp format")


class VehicleHandler:
    def create_vehicle(self, data):
        if hasattr(data, "make") and data.make is not None:
            data.make = data.make.strip()
        if hasattr(data, "model") and data.model is not None:
            data.model = data.model.strip()

        if not data.plate_number or data.plate_number.strip() == "":
            raise HTTPException(status_code=400, detail="plate_number must be non-empty")
        data.plate_number = data.plate_number.strip()

        if not (1950 <= data.year <= 2100):
            raise HTTPException(status_code=400, detail="year must be between 1950 and 2100")

        dao = VehicleDAO()
        try:
            created = dao.create_vehicle(
                VehicleCreate(
                    vehicle_type_id=data.vehicle_type_id,
                    vehicle_status_id=data.vehicle_status_id,
                    plate_number=data.plate_number,
                    make=data.make,
                    model=data.model,
                    year=data.year,
                )
            )
            return created
        except psycopg2.errors.ForeignKeyViolation:
            raise HTTPException(
                status_code=404, detail="vehicle_type_id or vehicle_status_id does not exist"
            )
        except psycopg2.errors.UniqueViolation:
            raise HTTPException(status_code=409, detail="plate_number already exists")

    def get_all_vehicles(self, limit, offset, status, plate_number):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="limit and offset must be non-negative")
        dao = VehicleDAO()
        return dao.get_all_vehicles(limit, offset, status, plate_number)

    def get_vehicle_by_id(self, vehicle_id: int):
        dao = VehicleDAO()
        result = dao.get_vehicle_by_id(vehicle_id)
        if result is None:
            raise HTTPException(status_code=404, detail="vehicle not found")
        return result

    def update_vehicle(self, vehicle_id: int, data):
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(status_code=400, detail="no fields provided for update")

        if "make" in payload and payload["make"] is not None:
            payload["make"] = payload["make"].strip()
        if "model" in payload and payload["model"] is not None:
            payload["model"] = payload["model"].strip()

        if "year" in payload and payload["year"] is not None:
            if not (1950 <= payload["year"] <= 2100):
                raise HTTPException(status_code=400, detail="year must be between 1950 and 2100")

        dao = VehicleDAO()
        try:
            updated = dao.update_vehicle(vehicle_id, VehicleUpdate(**payload))
            if updated is None:
                raise HTTPException(status_code=404, detail="vehicle not found")
            return updated
        except psycopg2.errors.ForeignKeyViolation:
            raise HTTPException(status_code=404, detail="referenced id does not exist")
        except psycopg2.errors.UniqueViolation:
            raise HTTPException(status_code=409, detail="plate_number already exists")

    def delete_vehicle(self, vehicle_id: int):
        dao = VehicleDAO()
        try:
            deleted = dao.delete_vehicle(vehicle_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="vehicle not found")
            return {"message": "Vehicle deleted successfully.", "vehicle_id": vehicle_id}
        except psycopg2.errors.ForeignKeyViolation:
            raise HTTPException(
                status_code=409,
                detail="cannot delete vehicle because it is referenced by other records",
            )

    def get_vehicle_current_location(self, vehicle_id: int):
        dao = VehicleDAO()
        result = dao.get_vehicle_current_location(vehicle_id)
        if result is None:
            raise HTTPException(status_code=404, detail="vehicle not found")
        if result == {}:
            return None
        return result

    def get_vehicle_pings(self, vehicle_id: int, limit: int, offset: int, from_ts, to_ts):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="limit and offset must be non-negative")
        f = _parse_ts(from_ts)
        t = _parse_ts(to_ts)
        if f is not None and t is not None and f > t:
            raise HTTPException(status_code=400, detail="invalid time range")

        dao = VehicleDAO()
        result = dao.get_vehicle_pings(vehicle_id, limit, offset, from_ts, to_ts)
        if result is None:
            raise HTTPException(status_code=404, detail="vehicle not found")
        return result

    def get_vehicle_trips(self, vehicle_id: int, limit: int, offset: int, from_ts, to_ts):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="limit and offset must be non-negative")
        f = _parse_ts(from_ts)
        t = _parse_ts(to_ts)
        if f is not None and t is not None and f > t:
            raise HTTPException(status_code=400, detail="invalid time range")

        dao = VehicleDAO()
        result = dao.get_vehicle_trips(vehicle_id, limit, offset, from_ts, to_ts)
        if result is None:
            raise HTTPException(status_code=404, detail="vehicle not found")
        return result


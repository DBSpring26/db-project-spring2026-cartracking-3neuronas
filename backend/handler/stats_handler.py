from typing import Optional
from datetime import datetime

from fastapi import HTTPException

from ..dao.stats_dao import StatsDAO


class StatsHandler:
    def get_pings_per_day(self, from_ts: Optional[str], to_ts: Optional[str]) -> dict:
        if from_ts is not None and from_ts != "":
            try:
                datetime.fromisoformat(from_ts)
            except ValueError:
                raise HTTPException(status_code=400, detail="invalid from_ts format")

        if to_ts is not None and to_ts != "":
            try:
                datetime.fromisoformat(to_ts)
            except ValueError:
                raise HTTPException(status_code=400, detail="invalid to_ts format")

        if from_ts and to_ts:
            if datetime.fromisoformat(from_ts) > datetime.fromisoformat(to_ts):
                raise HTTPException(status_code=400, detail="from_ts must be before to_ts")

        dao = StatsDAO()
        try:
            return dao.get_pings_per_day(from_ts, to_ts)
        except Exception:
            raise HTTPException(status_code=500, detail="internal server error")

from typing import Optional

from fastapi import HTTPException

from ..dao.stats_dao import StatsDAO


class StatsHandler:
    def get_pings_per_day(self, from_ts: Optional[str], to_ts: Optional[str]) -> dict:
        dao = StatsDAO()
        try:
            return dao.get_pings_per_day(from_ts, to_ts)
        except Exception:
            raise HTTPException(status_code=500, detail="internal server error")

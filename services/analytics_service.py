from database import get_db
from queries.dashboard_queries import (
    get_band_dashboard_stats,
    get_venue_owner_dashboard_stats,
)


def get_venue_owner_analytics(venue_owner_id: int) -> dict:
    with get_db() as db:
        return get_venue_owner_dashboard_stats(db, venue_owner_id)


def get_band_analytics(band_id: int) -> dict:
    with get_db() as db:
        return get_band_dashboard_stats(db, band_id)

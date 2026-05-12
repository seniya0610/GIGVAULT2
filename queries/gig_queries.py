import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models import Application, ApplicationStatus, GigListing, GigStatus


def get_open_gigs_filtered(
    db: Session,
    genre: Optional[str] = None,
    city: Optional[str] = None,
    date: Optional[datetime.date] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    band_id: Optional[int] = None,
) -> list[GigListing]:
    q = (
        db.query(GigListing)
        .filter(
            GigListing.gig_status == GigStatus.OPEN,
            GigListing.performance_date >= datetime.date.today(),
        )
    )

    if genre and genre != "All":
        q = q.filter(GigListing.genre_required.ilike(f"%{genre}%"))
    if city and city.strip():
        q = q.filter(GigListing.location_city.ilike(f"%{city.strip()}%"))
    if date:
        q = q.filter(GigListing.performance_date == date)
    if min_budget is not None and min_budget > 0:
        q = q.filter(GigListing.offered_pay >= min_budget)
    if max_budget is not None and max_budget > 0:
        q = q.filter(GigListing.offered_pay <= max_budget)

    return q.order_by(GigListing.performance_date.asc()).all()


def get_venue_owner_gig_stats(db: Session, venue_owner_id: int) -> dict:
    from sqlalchemy import func

    gigs = (
        db.query(GigListing.gig_status, func.count(GigListing.gig_id).label("cnt"))
        .filter(GigListing.venue_owner_id == venue_owner_id)
        .group_by(GigListing.gig_status)
        .all()
    )
    stats = {row.gig_status: row.cnt for row in gigs}

    pending_apps = (
        db.query(func.count(Application.application_id))
        .join(Application.gig)
        .filter(
            GigListing.venue_owner_id == venue_owner_id,
            Application.application_status == ApplicationStatus.PENDING,
        )
        .scalar()
        or 0
    )

    return {
        "open": stats.get(GigStatus.OPEN, 0),
        "filled": stats.get(GigStatus.FILLED, 0),
        "completed": stats.get(GigStatus.COMPLETED, 0),
        "cancelled": stats.get(GigStatus.CANCELLED, 0),
        "total": sum(stats.values()),
        "pending_applications": pending_apps,
    }

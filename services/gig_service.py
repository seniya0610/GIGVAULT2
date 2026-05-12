import datetime
from typing import Optional

from database import get_db
from models import BookingStatus, GigListing, GigStatus


def create_gig(
    venue_owner_id: int,
    gig_title: str,
    description: str,
    genre_required: str,
    location_city: str,
    performance_date: datetime.date,
    performance_time: Optional[datetime.time],
    duration_hours: Optional[float],
    offered_pay: float,
) -> GigListing:
    with get_db() as db:
        existing = (
            db.query(GigListing)
            .filter(
                GigListing.venue_owner_id == venue_owner_id,
                GigListing.performance_date == performance_date,
                GigListing.gig_status != GigStatus.CANCELLED,
            )
            .first()
        )
        if existing:
            raise ValueError(
                f"You already have an active gig on {performance_date.strftime('%b %d, %Y')}. "
                f"Cancel it first, or choose a different date."
            )

        if performance_date < datetime.date.today():
            raise ValueError("Performance date cannot be in the past.")

        if offered_pay <= 0:
            raise ValueError("Offered pay must be greater than zero.")

        gig = GigListing(
            venue_owner_id=venue_owner_id,
            gig_title=gig_title.strip(),
            description=description.strip() if description else None,
            genre_required=genre_required,
            location_city=location_city.strip(),
            performance_date=performance_date,
            performance_time=performance_time,
            duration_hours=duration_hours,
            offered_pay=offered_pay,
            gig_status=GigStatus.OPEN,
        )
        db.add(gig)
        db.commit()
        db.refresh(gig)
        return gig


def update_gig(
    gig_id: int,
    venue_owner_id: int,
    gig_title: str,
    description: str,
    genre_required: str,
    location_city: str,
    performance_time: Optional[datetime.time],
    duration_hours: Optional[float],
    offered_pay: float,
) -> GigListing:
    with get_db() as db:
        gig = (
            db.query(GigListing)
            .filter(
                GigListing.gig_id == gig_id,
                GigListing.venue_owner_id == venue_owner_id,
                GigListing.gig_status == GigStatus.OPEN,
            )
            .first()
        )
        if not gig:
            raise ValueError("Gig not found or cannot be edited in its current state.")
        if offered_pay <= 0:
            raise ValueError("Offered pay must be greater than zero.")

        gig.gig_title = gig_title.strip()
        gig.description = description.strip() if description else None
        gig.genre_required = genre_required
        gig.location_city = location_city.strip()
        gig.performance_time = performance_time
        gig.duration_hours = duration_hours
        gig.offered_pay = offered_pay

        db.commit()
        db.refresh(gig)
        return gig


def cancel_gig(gig_id: int, venue_owner_id: int) -> GigListing:
    with get_db() as db:
        gig = (
            db.query(GigListing)
            .filter(
                GigListing.gig_id == gig_id,
                GigListing.venue_owner_id == venue_owner_id,
                GigListing.gig_status.in_([GigStatus.OPEN]),
            )
            .first()
        )
        if not gig:
            raise ValueError(
                "Gig not found, already booked, or cannot be cancelled."
            )
        gig.gig_status = GigStatus.CANCELLED
        db.commit()
        db.refresh(gig)
        return gig


def complete_gig(gig_id: int, venue_owner_id: int) -> GigListing:
    with get_db() as db:
        gig = (
            db.query(GigListing)
            .filter(
                GigListing.gig_id == gig_id,
                GigListing.venue_owner_id == venue_owner_id,
                GigListing.gig_status == GigStatus.FILLED,
            )
            .first()
        )
        if not gig:
            raise ValueError("Gig not found or not in a Filled state.")

        gig.gig_status = GigStatus.COMPLETED

        for booking in gig.bookings:
            booking.contract_status = BookingStatus.COMPLETED

        db.commit()
        db.refresh(gig)
        return gig


def get_venue_owner_gigs(venue_owner_id: int) -> list[GigListing]:
    with get_db() as db:
        return (
            db.query(GigListing)
            .filter(GigListing.venue_owner_id == venue_owner_id)
            .order_by(GigListing.performance_date.desc())
            .all()
        )


def get_gig_by_id(gig_id: int) -> GigListing | None:
    with get_db() as db:
        return db.query(GigListing).filter(GigListing.gig_id == gig_id).first()

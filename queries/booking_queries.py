from sqlalchemy.orm import Session

from models import Band, BookingContract, BookingStatus, GigListing, User


def get_active_bookings_for_venue_owner(db: Session, venue_owner_id: int) -> list:
    return (
        db.query(BookingContract, GigListing, Band)
        .join(GigListing, BookingContract.gig_id == GigListing.gig_id)
        .join(Band, BookingContract.band_id == Band.band_id)
        .filter(
            BookingContract.venue_owner_id == venue_owner_id,
            BookingContract.contract_status == BookingStatus.ACTIVE,
        )
        .order_by(BookingContract.performance_date.asc())
        .all()
    )


def get_all_bookings_for_venue_owner(db: Session, venue_owner_id: int) -> list:
    return (
        db.query(BookingContract, GigListing, Band)
        .join(GigListing, BookingContract.gig_id == GigListing.gig_id)
        .join(Band, BookingContract.band_id == Band.band_id)
        .filter(BookingContract.venue_owner_id == venue_owner_id)
        .order_by(BookingContract.performance_date.desc())
        .all()
    )


def get_all_bookings_for_band(db: Session, band_id: int) -> list:
    return (
        db.query(BookingContract, GigListing, User)
        .join(GigListing, BookingContract.gig_id == GigListing.gig_id)
        .join(User, BookingContract.venue_owner_id == User.user_id)
        .filter(BookingContract.band_id == band_id)
        .order_by(BookingContract.performance_date.desc())
        .all()
    )

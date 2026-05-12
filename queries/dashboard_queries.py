import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    Application,
    ApplicationStatus,
    Band,
    BookingContract,
    BookingStatus,
    GigListing,
    GigStatus,
    Payment,
    PaymentStatus,
)


def get_venue_owner_dashboard_stats(db: Session, venue_owner_id: int) -> dict:
    gig_stats = (
        db.query(GigListing.gig_status, func.count(GigListing.gig_id))
        .filter(GigListing.venue_owner_id == venue_owner_id)
        .group_by(GigListing.gig_status)
        .all()
    )
    gig_map = {}
    for status, cnt in gig_stats:
        gig_map[status.value if hasattr(status, "value") else status] = cnt

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

    total_committed = (
        db.query(func.sum(BookingContract.agreed_fee))
        .filter(
            BookingContract.venue_owner_id == venue_owner_id,
            BookingContract.contract_status.in_([BookingStatus.ACTIVE, BookingStatus.COMPLETED]),
        )
        .scalar()
        or 0.0
    )

    overdue_count = (
        db.query(func.count(Payment.payment_id))
        .filter(
            Payment.venue_owner_id == venue_owner_id,
            Payment.payment_status == PaymentStatus.PENDING,
        )
        .scalar()
        or 0
    )

    upcoming = (
        db.query(func.count(GigListing.gig_id))
        .filter(
            GigListing.venue_owner_id == venue_owner_id,
            GigListing.gig_status == GigStatus.FILLED,
            GigListing.performance_date >= datetime.date.today(),
        )
        .scalar()
        or 0
    )

    return {
        "total_gigs": sum(gig_map.values()),
        "open_gigs": gig_map.get("Open", 0),
        "filled_gigs": gig_map.get("Filled", 0),
        "completed_gigs": gig_map.get("Completed", 0),
        "cancelled_gigs": gig_map.get("Cancelled", 0),
        "pending_applications": pending_apps,
        "total_committed": float(total_committed),
        "overdue_payments": overdue_count,
        "upcoming_performances": upcoming,
    }


def get_band_dashboard_stats(db: Session, band_id: int) -> dict:
    app_stats = (
        db.query(Application.application_status, func.count(Application.application_id))
        .filter(Application.band_id == band_id)
        .group_by(Application.application_status)
        .all()
    )
    app_map = {}
    for status, cnt in app_stats:
        app_map[status.value if hasattr(status, "value") else status] = cnt

    total_earned = (
        db.query(func.sum(Payment.amount))
        .filter(
            Payment.band_id == band_id,
            Payment.payment_status == PaymentStatus.COMPLETED,
        )
        .scalar()
        or 0.0
    )

    pending_pay = (
        db.query(func.sum(Payment.amount))
        .filter(
            Payment.band_id == band_id,
            Payment.payment_status == PaymentStatus.PENDING,
        )
        .scalar()
        or 0.0
    )

    upcoming = (
        db.query(func.count(BookingContract.booking_id))
        .join(BookingContract.gig)
        .filter(
            BookingContract.band_id == band_id,
            BookingContract.contract_status == BookingStatus.ACTIVE,
            GigListing.performance_date >= datetime.date.today(),
        )
        .scalar()
        or 0
    )

    overdue_count = (
        db.query(func.count(Payment.payment_id))
        .filter(
            Payment.band_id == band_id,
            Payment.payment_status == PaymentStatus.PENDING,
        )
        .scalar()
        or 0
    )

    return {
        "total_applications": sum(app_map.values()),
        "pending_applications": app_map.get("Pending", 0),
        "accepted_applications": app_map.get("Accepted", 0),
        "rejected_applications": app_map.get("Rejected", 0),
        "upcoming_gigs": upcoming,
        "total_earned": float(total_earned),
        "pending_payment": float(pending_pay),
        "overdue_payments": overdue_count,
    }

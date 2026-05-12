import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Band, BookingContract, GigListing, Payment, PaymentStatus, User


def get_venue_owner_payment_summary(db: Session, venue_owner_id: int) -> dict:
    rows = (
        db.query(Payment.payment_status, func.count(Payment.payment_id), func.sum(Payment.amount))
        .filter(Payment.venue_owner_id == venue_owner_id)
        .group_by(Payment.payment_status)
        .all()
    )
    summary: dict = {
        "pending_count": 0,
        "pending_amount": 0.0,
        "completed_count": 0,
        "completed_amount": 0.0,
        "failed_count": 0,
        "failed_amount": 0.0,
        "refunded_count": 0,
        "refunded_amount": 0.0,
        "total_amount": 0.0,
    }
    for status, cnt, total in rows:
        status_val = status.value if hasattr(status, "value") else status
        s = status_val.lower()
        summary[f"{s}_count"] = cnt or 0
        summary[f"{s}_amount"] = float(total or 0)
        summary["total_amount"] += float(total or 0)
    return summary


def get_band_payment_summary(db: Session, band_id: int) -> dict:
    rows = (
        db.query(Payment.payment_status, func.count(Payment.payment_id), func.sum(Payment.amount))
        .filter(Payment.band_id == band_id)
        .group_by(Payment.payment_status)
        .all()
    )
    summary: dict = {
        "pending_count": 0,
        "pending_amount": 0.0,
        "completed_count": 0,
        "completed_amount": 0.0,
        "failed_count": 0,
        "failed_amount": 0.0,
        "total_earned": 0.0,
    }
    for status, cnt, total in rows:
        status_val = status.value if hasattr(status, "value") else status
        s = status_val.lower()
        summary[f"{s}_count"] = cnt or 0
        summary[f"{s}_amount"] = float(total or 0)
        if status_val == "Completed":
            summary["total_earned"] += float(total or 0)
    return summary


def get_venue_owner_payments_with_details(db: Session, venue_owner_id: int) -> list:
    return (
        db.query(Payment, Band, GigListing)
        .join(BookingContract, Payment.booking_id == BookingContract.booking_id)
        .join(GigListing, BookingContract.gig_id == GigListing.gig_id)
        .join(Band, Payment.band_id == Band.band_id)
        .filter(Payment.venue_owner_id == venue_owner_id)
        .order_by(Payment.payment_date.asc())
        .all()
    )


def get_band_payments_with_details(db: Session, band_id: int) -> list:
    return (
        db.query(Payment, User, GigListing)
        .join(BookingContract, Payment.booking_id == BookingContract.booking_id)
        .join(GigListing, BookingContract.gig_id == GigListing.gig_id)
        .join(User, Payment.venue_owner_id == User.user_id)
        .filter(Payment.band_id == band_id)
        .order_by(Payment.payment_date.asc())
        .all()
    )

import datetime

from database import get_db
from models import Payment, PaymentStatus


def mark_payment_completed(payment_id: int, venue_owner_id: int, notes: str = "") -> Payment:
    with get_db() as db:
        payment = (
            db.query(Payment)
            .filter(
                Payment.payment_id == payment_id,
                Payment.venue_owner_id == venue_owner_id,
                Payment.payment_status.in_([PaymentStatus.PENDING]),
            )
            .first()
        )
        if not payment:
            raise ValueError("Payment not found or already completed/cancelled.")
        payment.payment_status = PaymentStatus.COMPLETED
        payment.payment_date = datetime.datetime.utcnow()
        if notes:
            payment.notes = notes
        db.commit()
        db.refresh(payment)
        return payment


def get_venue_owner_payments(venue_owner_id: int) -> list[Payment]:
    with get_db() as db:
        return (
            db.query(Payment)
            .filter(Payment.venue_owner_id == venue_owner_id)
            .order_by(Payment.payment_date.asc())
            .all()
        )


def get_band_payments(band_id: int) -> list[Payment]:
    with get_db() as db:
        return (
            db.query(Payment)
            .filter(Payment.band_id == band_id)
            .order_by(Payment.payment_date.asc())
            .all()
        )

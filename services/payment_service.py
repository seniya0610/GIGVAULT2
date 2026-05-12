import datetime

from database import get_db
from models import Payment, PaymentStatus


def refresh_overdue_payments(db=None) -> int:
    close_after = db is None
    if db is None:
        from database import get_session_factory
        factory = get_session_factory()
        db = factory()

    try:
        today = datetime.date.today()
        count = (
            db.query(Payment)
            .filter(
                Payment.status == PaymentStatus.PENDING,
                Payment.due_date < today,
            )
            .update(
                {"status": PaymentStatus.OVERDUE.value},
                synchronize_session=False,
            )
        )
        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        if close_after:
            db.close()


def mark_payment_paid(payment_id: int, client_id: int, notes: str = "") -> Payment:
    with get_db() as db:
        payment = (
            db.query(Payment)
            .filter(
                Payment.id == payment_id,
                Payment.client_id == client_id,
                Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.OVERDUE]),
            )
            .first()
        )
        if not payment:
            raise ValueError("Payment not found or already paid/cancelled.")
        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.datetime.utcnow()
        if notes:
            payment.notes = notes
        db.commit()
        db.refresh(payment)
        return payment


def get_client_payments(client_id: int) -> list[Payment]:
    with get_db() as db:
        refresh_overdue_payments(db)
        return (
            db.query(Payment)
            .filter(Payment.client_id == client_id)
            .order_by(Payment.due_date.asc())
            .all()
        )


def get_musician_payments(musician_id: int) -> list[Payment]:
    with get_db() as db:
        refresh_overdue_payments(db)
        return (
            db.query(Payment)
            .filter(Payment.musician_id == musician_id)
            .order_by(Payment.due_date.asc())
            .all()
        )

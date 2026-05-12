import datetime

from config import PAYMENT_DUE_DAYS
from database import get_db
from models import (
    Application,
    ApplicationStatus,
    AvailabilityCalendar,
    BookingContract,
    BookingStatus,
    GigListing,
    GigStatus,
    Payment,
    PaymentStatus,
)


def accept_application(application_id: int, client_id: int) -> BookingContract:
    with get_db() as db:
        app = (
            db.query(Application)
            .join(Application.gig)
            .filter(
                Application.id == application_id,
                Application.status == ApplicationStatus.PENDING,
                GigListing.client_id == client_id,
                GigListing.status == GigStatus.OPEN,
            )
            .first()
        )
        if not app:
            raise ValueError(
                "Application not found, already processed, or gig is no longer open."
            )

        gig = app.gig

        busy = (
            db.query(AvailabilityCalendar)
            .filter(
                AvailabilityCalendar.musician_id == app.musician_id,
                AvailabilityCalendar.date == gig.performance_date,
                AvailabilityCalendar.is_available == False,
            )
            .first()
        )
        if busy:
            raise ValueError(
                "This musician is no longer available on the performance date."
            )

        app.status = ApplicationStatus.ACCEPTED

        db.query(Application).filter(
            Application.gig_id == gig.id,
            Application.id != application_id,
            Application.status == ApplicationStatus.PENDING,
        ).update({"status": ApplicationStatus.REJECTED.value}, synchronize_session=False)

        gig.status = GigStatus.BOOKED

        agreed = float(app.proposed_rate) if app.proposed_rate else float(gig.budget)
        booking = BookingContract(
            gig_id=gig.id,
            client_id=client_id,
            musician_id=app.musician_id,
            agreed_amount=agreed,
            status=BookingStatus.ACTIVE,
        )
        db.add(booking)
        db.flush()

        avail_record = (
            db.query(AvailabilityCalendar)
            .filter(
                AvailabilityCalendar.musician_id == app.musician_id,
                AvailabilityCalendar.date == gig.performance_date,
            )
            .first()
        )
        if avail_record:
            avail_record.is_available = False
            avail_record.booking_id = booking.id
        else:
            db.add(
                AvailabilityCalendar(
                    musician_id=app.musician_id,
                    date=gig.performance_date,
                    is_available=False,
                    booking_id=booking.id,
                )
            )

        due = gig.performance_date + datetime.timedelta(days=PAYMENT_DUE_DAYS)
        payment = Payment(
            booking_id=booking.id,
            client_id=client_id,
            musician_id=app.musician_id,
            amount=agreed,
            status=PaymentStatus.PENDING,
            due_date=due,
        )
        db.add(payment)
        db.commit()
        db.refresh(booking)
        return booking


def reject_application(application_id: int, client_id: int) -> Application:
    with get_db() as db:
        app = (
            db.query(Application)
            .join(Application.gig)
            .filter(
                Application.id == application_id,
                Application.status == ApplicationStatus.PENDING,
                GigListing.client_id == client_id,
            )
            .first()
        )
        if not app:
            raise ValueError("Application not found.")
        app.status = ApplicationStatus.REJECTED
        db.commit()
        db.refresh(app)
        return app


def cancel_booking(booking_id: int, client_id: int) -> BookingContract:
    with get_db() as db:
        booking = (
            db.query(BookingContract)
            .filter(
                BookingContract.id == booking_id,
                BookingContract.client_id == client_id,
                BookingContract.status == BookingStatus.ACTIVE,
            )
            .first()
        )
        if not booking:
            raise ValueError("Booking not found or already finalised.")

        booking.status = BookingStatus.CANCELLED
        booking.gig.status = GigStatus.CANCELLED

        if booking.payment:
            booking.payment.status = PaymentStatus.CANCELLED

        avail = (
            db.query(AvailabilityCalendar)
            .filter(AvailabilityCalendar.booking_id == booking_id)
            .first()
        )
        if avail:
            avail.is_available = True
            avail.booking_id = None

        db.commit()
        db.refresh(booking)
        return booking


def complete_booking(booking_id: int, client_id: int) -> BookingContract:
    with get_db() as db:
        booking = (
            db.query(BookingContract)
            .filter(
                BookingContract.id == booking_id,
                BookingContract.client_id == client_id,
                BookingContract.status == BookingStatus.ACTIVE,
            )
            .first()
        )
        if not booking:
            raise ValueError("Booking not found.")
        booking.status = BookingStatus.COMPLETED
        booking.gig.status = GigStatus.COMPLETED
        db.commit()
        db.refresh(booking)
        return booking


def get_client_bookings(client_id: int) -> list[BookingContract]:
    with get_db() as db:
        return (
            db.query(BookingContract)
            .join(BookingContract.gig)
            .filter(BookingContract.client_id == client_id)
            .order_by(GigListing.performance_date.desc())
            .all()
        )


def get_musician_bookings(musician_id: int) -> list[BookingContract]:
    with get_db() as db:
        return (
            db.query(BookingContract)
            .join(BookingContract.gig)
            .filter(BookingContract.musician_id == musician_id)
            .order_by(GigListing.performance_date.desc())
            .all()
        )

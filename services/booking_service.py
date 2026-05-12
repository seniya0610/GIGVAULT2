import datetime

from database import get_db
from models import (
    Application,
    ApplicationStatus,
    BookingContract,
    BookingStatus,
    GigListing,
    GigStatus,
)


def accept_application(application_id: int, venue_owner_id: int) -> BookingContract:
    with get_db() as db:
        app = (
            db.query(Application)
            .join(Application.gig)
            .filter(
                Application.application_id == application_id,
                Application.application_status == ApplicationStatus.PENDING,
                GigListing.venue_owner_id == venue_owner_id,
                GigListing.gig_status == GigStatus.OPEN,
            )
            .first()
        )
        if not app:
            raise ValueError(
                "Application not found, already processed, or gig is no longer open."
            )

        gig = app.gig

        app.application_status = ApplicationStatus.ACCEPTED

        db.query(Application).filter(
            Application.gig_id == gig.gig_id,
            Application.application_id != application_id,
            Application.application_status == ApplicationStatus.PENDING,
        ).update({"application_status": ApplicationStatus.REJECTED.value}, synchronize_session=False)

        gig.gig_status = GigStatus.FILLED

        agreed = float(gig.offered_pay)
        booking = BookingContract(
            gig_id=gig.gig_id,
            venue_owner_id=venue_owner_id,
            band_id=app.band_id,
            agreed_fee=agreed,
            contract_status=BookingStatus.ACTIVE,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking


def reject_application(application_id: int, venue_owner_id: int) -> Application:
    with get_db() as db:
        app = (
            db.query(Application)
            .join(Application.gig)
            .filter(
                Application.application_id == application_id,
                Application.application_status == ApplicationStatus.PENDING,
                GigListing.venue_owner_id == venue_owner_id,
            )
            .first()
        )
        if not app:
            raise ValueError("Application not found.")
        app.application_status = ApplicationStatus.REJECTED
        db.commit()
        db.refresh(app)
        return app


def cancel_booking(booking_id: int, venue_owner_id: int) -> BookingContract:
    with get_db() as db:
        booking = (
            db.query(BookingContract)
            .filter(
                BookingContract.booking_id == booking_id,
                BookingContract.venue_owner_id == venue_owner_id,
                BookingContract.contract_status == BookingStatus.ACTIVE,
            )
            .first()
        )
        if not booking:
            raise ValueError("Booking not found or already finalised.")

        booking.contract_status = BookingStatus.CANCELLED
        booking.gig.gig_status = GigStatus.CANCELLED

        db.commit()
        db.refresh(booking)
        return booking


def complete_booking(booking_id: int, venue_owner_id: int) -> BookingContract:
    with get_db() as db:
        booking = (
            db.query(BookingContract)
            .filter(
                BookingContract.booking_id == booking_id,
                BookingContract.venue_owner_id == venue_owner_id,
                BookingContract.contract_status == BookingStatus.ACTIVE,
            )
            .first()
        )
        if not booking:
            raise ValueError("Booking not found.")
        booking.contract_status = BookingStatus.COMPLETED
        booking.gig.gig_status = GigStatus.COMPLETED
        db.commit()
        db.refresh(booking)
        return booking


def get_venue_owner_bookings(venue_owner_id: int) -> list[BookingContract]:
    with get_db() as db:
        return (
            db.query(BookingContract)
            .join(BookingContract.gig)
            .filter(BookingContract.venue_owner_id == venue_owner_id)
            .order_by(GigListing.performance_date.desc())
            .all()
        )


def get_band_bookings(band_id: int) -> list[BookingContract]:
    with get_db() as db:
        return (
            db.query(BookingContract)
            .join(BookingContract.gig)
            .filter(BookingContract.band_id == band_id)
            .order_by(GigListing.performance_date.desc())
            .all()
        )

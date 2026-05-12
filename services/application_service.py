import datetime
from typing import Optional

from database import get_db
from models import Application, ApplicationStatus, GigListing, GigStatus


def apply_to_gig(
    band_id: int,
    gig_id: int,
    cover_letter: str,
) -> Application:
    with get_db() as db:
        gig = (
            db.query(GigListing)
            .filter(
                GigListing.gig_id == gig_id,
                GigListing.gig_status == GigStatus.OPEN,
            )
            .first()
        )
        if not gig:
            raise ValueError("This gig is no longer available.")

        if gig.performance_date < datetime.date.today():
            raise ValueError("Cannot apply to a gig with a past performance date.")

        duplicate = (
            db.query(Application)
            .filter(
                Application.gig_id == gig_id,
                Application.band_id == band_id,
                Application.application_status != ApplicationStatus.WITHDRAWN,
            )
            .first()
        )
        if duplicate:
            raise ValueError("Your band has already applied to this gig.")

        app = Application(
            gig_id=gig_id,
            band_id=band_id,
            cover_letter=cover_letter.strip() if cover_letter else None,
            application_status=ApplicationStatus.PENDING,
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        return app


def withdraw_application(application_id: int, band_id: int) -> Application:
    with get_db() as db:
        app = (
            db.query(Application)
            .filter(
                Application.application_id == application_id,
                Application.band_id == band_id,
                Application.application_status == ApplicationStatus.PENDING,
            )
            .first()
        )
        if not app:
            raise ValueError("Application not found or cannot be withdrawn.")
        app.application_status = ApplicationStatus.WITHDRAWN
        db.commit()
        db.refresh(app)
        return app


def get_band_applications(band_id: int) -> list[Application]:
    with get_db() as db:
        return (
            db.query(Application)
            .join(Application.gig)
            .filter(Application.band_id == band_id)
            .order_by(Application.application_date.desc())
            .all()
        )


def get_gig_applications(gig_id: int, venue_owner_id: int) -> list[Application]:
    with get_db() as db:
        return (
            db.query(Application)
            .join(Application.gig)
            .filter(
                Application.gig_id == gig_id,
                GigListing.venue_owner_id == venue_owner_id,
                Application.application_status == ApplicationStatus.PENDING,
            )
            .order_by(Application.application_date.asc())
            .all()
        )


def get_all_venue_owner_pending_applications(venue_owner_id: int) -> list[Application]:
    with get_db() as db:
        return (
            db.query(Application)
            .join(Application.gig)
            .filter(
                GigListing.venue_owner_id == venue_owner_id,
                Application.application_status == ApplicationStatus.PENDING,
            )
            .order_by(Application.application_date.asc())
            .all()
        )

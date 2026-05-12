import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    CLIENT = "client"
    MUSICIAN = "musician"


class GigStatus(str, enum.Enum):
    OPEN = "Open"
    BOOKED = "Booked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ApplicationStatus(str, enum.Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


class BookingStatus(str, enum.Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole, native_enum=False), nullable=False)
    city = Column(String(100))
    bio = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client_profile = relationship(
        "ClientProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    musician_profile = relationship(
        "MusicianProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    gig_listings = relationship(
        "GigListing",
        foreign_keys="GigListing.client_id",
        back_populates="client",
        cascade="all, delete-orphan",
    )
    applications = relationship(
        "Application",
        foreign_keys="Application.musician_id",
        back_populates="musician",
        cascade="all, delete-orphan",
    )
    client_bookings = relationship(
        "BookingContract",
        foreign_keys="BookingContract.client_id",
        back_populates="client",
    )
    musician_bookings = relationship(
        "BookingContract",
        foreign_keys="BookingContract.musician_id",
        back_populates="musician",
    )
    availability_slots = relationship(
        "AvailabilityCalendar",
        back_populates="musician",
        cascade="all, delete-orphan",
    )
    client_payments = relationship(
        "Payment",
        foreign_keys="Payment.client_id",
        back_populates="client",
    )
    musician_payments = relationship(
        "Payment",
        foreign_keys="Payment.musician_id",
        back_populates="musician",
    )
    bands_led = relationship(
        "Band",
        foreign_keys="Band.leader_id",
        back_populates="leader",
    )
    band_memberships = relationship(
        "BandMember",
        foreign_keys="BandMember.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    setlists = relationship(
        "Setlist",
        back_populates="musician",
        cascade="all, delete-orphan",
    )


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    venue_name = Column(String(200), nullable=False, default="")
    venue_type = Column(String(100), default="Bar")
    genre_specialization = Column(String(300), default="")
    city = Column(String(100), nullable=False, default="")
    address = Column(String(300))
    capacity = Column(Integer)
    description = Column(Text)
    website = Column(String(300))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="client_profile")


class MusicianProfile(Base):
    __tablename__ = "musician_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    stage_name = Column(String(200), default="")
    genres = Column(String(300), default="")
    instruments = Column(String(300), default="")
    hourly_rate = Column(Numeric(10, 2), default=0)
    years_experience = Column(Integer, default=0)
    soundcloud_url = Column(String(300))
    spotify_url = Column(String(300))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="musician_profile")


class Band(Base):
    __tablename__ = "bands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    leader_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name = Column(String(200), nullable=False)
    genre = Column(String(200))
    description = Column(Text)
    city = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    leader = relationship("User", foreign_keys=[leader_id], back_populates="bands_led")
    members = relationship("BandMember", back_populates="band", cascade="all, delete-orphan")


class BandMember(Base):
    __tablename__ = "band_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    band_id = Column(
        Integer, ForeignKey("bands.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_in_band = Column(String(100))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("band_id", "user_id", name="uq_band_member"),
    )

    band = relationship("Band", back_populates="members")
    user = relationship("User", back_populates="band_memberships")


class GigListing(Base):
    __tablename__ = "gig_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(300), nullable=False)
    description = Column(Text)
    genre = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    performance_date = Column(Date, nullable=False)
    start_time = Column(Time)
    end_time = Column(Time)
    duration_hours = Column(Numeric(4, 2))
    budget = Column(Numeric(10, 2), nullable=False)
    requirements = Column(Text)
    status = Column(
        SAEnum(GigStatus, native_enum=False),
        default=GigStatus.OPEN,
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_gig_client_date", "client_id", "performance_date"),
        Index("ix_gig_city_genre_date", "city", "genre", "performance_date"),
        Index("ix_gig_status", "status"),
        Index("ix_gig_performance_date", "performance_date"),
    )

    client = relationship(
        "User", foreign_keys=[client_id], back_populates="gig_listings"
    )
    applications = relationship(
        "Application", back_populates="gig", cascade="all, delete-orphan"
    )
    booking = relationship(
        "BookingContract", back_populates="gig", uselist=False
    )


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gig_id = Column(
        Integer, ForeignKey("gig_listings.id", ondelete="CASCADE"), nullable=False
    )
    musician_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message = Column(Text)
    proposed_rate = Column(Numeric(10, 2))
    status = Column(
        SAEnum(ApplicationStatus, native_enum=False),
        default=ApplicationStatus.PENDING,
        nullable=False,
    )
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("gig_id", "musician_id", name="uq_application_gig_musician"),
        Index("ix_application_musician_status", "musician_id", "status"),
        Index("ix_application_gig_status", "gig_id", "status"),
    )

    gig = relationship("GigListing", back_populates="applications")
    musician = relationship(
        "User", foreign_keys=[musician_id], back_populates="applications"
    )


class BookingContract(Base):
    __tablename__ = "bookings_contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gig_id = Column(
        Integer,
        ForeignKey("gig_listings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    client_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    musician_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    agreed_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(
        SAEnum(BookingStatus, native_enum=False),
        default=BookingStatus.ACTIVE,
        nullable=False,
    )
    booked_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)

    __table_args__ = (
        Index("ix_booking_client", "client_id"),
        Index("ix_booking_musician", "musician_id"),
        Index("ix_booking_status", "status"),
    )

    gig = relationship("GigListing", back_populates="booking")
    client = relationship(
        "User", foreign_keys=[client_id], back_populates="client_bookings"
    )
    musician = relationship(
        "User", foreign_keys=[musician_id], back_populates="musician_bookings"
    )
    payment = relationship(
        "Payment",
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AvailabilityCalendar(Base):
    __tablename__ = "availability_calendar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    musician_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    date = Column(Date, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    booking_id = Column(
        Integer,
        ForeignKey("bookings_contracts.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "musician_id", "date", name="uq_availability_musician_date"
        ),
        Index("ix_availability_musician_date", "musician_id", "date"),
    )

    musician = relationship("User", back_populates="availability_slots")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(
        Integer,
        ForeignKey("bookings_contracts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    client_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    musician_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(
        SAEnum(PaymentStatus, native_enum=False),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_payment_client_status", "client_id", "status"),
        Index("ix_payment_musician_status", "musician_id", "status"),
        Index("ix_payment_due_date", "due_date"),
    )

    booking = relationship("BookingContract", back_populates="payment")
    client = relationship(
        "User", foreign_keys=[client_id], back_populates="client_payments"
    )
    musician = relationship(
        "User", foreign_keys=[musician_id], back_populates="musician_payments"
    )


class ReviewDispute(Base):
    __tablename__ = "reviews_disputes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(
        Integer, ForeignKey("bookings_contracts.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reviewee_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating = Column(Integer)
    comment = Column(Text)
    is_dispute = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "booking_id", "reviewer_id", name="uq_review_booking_reviewer"
        ),
    )


class Setlist(Base):
    __tablename__ = "setlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    musician_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    musician = relationship("User", back_populates="setlists")
    songs = relationship(
        "SetlistSong", back_populates="setlist", cascade="all, delete-orphan"
    )


class SetlistSong(Base):
    __tablename__ = "setlist_songs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    setlist_id = Column(
        Integer, ForeignKey("setlists.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(300), nullable=False)
    artist = Column(String(200))
    duration_minutes = Column(Integer)
    order_index = Column(Integer, default=0)

    setlist = relationship("Setlist", back_populates="songs")


class RecruitmentAd(Base):
    __tablename__ = "recruitment_ads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    poster_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(300), nullable=False)
    description = Column(Text)
    genre = Column(String(200))
    city = Column(String(100))
    instruments_needed = Column(String(300))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

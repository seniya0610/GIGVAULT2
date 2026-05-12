import enum

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
    MUSICIAN = "Musician"
    VENUE_OWNER = "Venue_Owner"
    ADMIN = "Admin"


class GigStatus(str, enum.Enum):
    OPEN = "Open"
    FILLED = "Filled"
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
    COMPLETED = "Completed"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class DepositStatus(str, enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"


class AdStatus(str, enum.Enum):
    ACTIVE = "Active"
    FILLED = "Filled"
    CLOSED = "Closed"


class ReviewType(str, enum.Enum):
    REVIEW = "Review"
    DISPUTE = "Dispute"


class ReviewStatus(str, enum.Enum):
    OPEN = "Open"
    RESOLVED = "Resolved"
    PENDING_REVIEW = "Pending_Review"


class ExperienceLevel(str, enum.Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    PROFESSIONAL = "Professional"


class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(15))
    role = Column(SAEnum(UserRole, native_enum=False), nullable=False)
    profile_picture_url = Column(Text)
    bio = Column(Text)
    city = Column(String(100))
    zip_code = Column(String(10))
    account_created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    bands_led = relationship("Band", back_populates="leader")
    band_memberships = relationship("BandMember", back_populates="user")
    gig_listings = relationship("GigListing", back_populates="venue_owner")
    bookings_as_venue = relationship("BookingContract", foreign_keys="BookingContract.venue_owner_id", back_populates="venue_owner")
    payments_as_venue = relationship("Payment", foreign_keys="Payment.venue_owner_id", back_populates="venue_owner")
    availability = relationship("AvailabilityCalendar", back_populates="user")
    recruitment_ads_posted = relationship("RecruitmentAd", back_populates="posted_by")
    reviews_given = relationship("ReviewDispute", foreign_keys="ReviewDispute.reviewer_id", back_populates="reviewer")
    reviews_received = relationship("ReviewDispute", foreign_keys="ReviewDispute.reviewee_id", back_populates="reviewee")


class Band(Base):
    __tablename__ = "Bands"

    band_id = Column(Integer, primary_key=True, autoincrement=True)
    band_name = Column(String(150), nullable=False)
    leader_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    genre = Column(String(100), nullable=False)
    bio = Column(Text)
    profile_picture_url = Column(Text)
    member_count = Column(Integer, default=1)
    city = Column(String(100))
    zip_code = Column(String(10))
    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    leader = relationship("User", back_populates="bands_led")
    members = relationship("BandMember", back_populates="band")
    applications = relationship("Application", back_populates="band")
    bookings = relationship("BookingContract", back_populates="band")
    payments = relationship("Payment", back_populates="band")
    recruitment_ads = relationship("RecruitmentAd", back_populates="band")
    setlists = relationship("Setlist", back_populates="band")


class BandMember(Base):
    __tablename__ = "Band_Members"

    member_id = Column(Integer, primary_key=True, autoincrement=True)
    band_id = Column(Integer, ForeignKey("Bands.band_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    instrument = Column(String(100), nullable=False)
    role_in_band = Column(String(50))
    joined_date = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("band_id", "user_id"),
    )

    band = relationship("Band", back_populates="members")
    user = relationship("User", back_populates="band_memberships")


class GigListing(Base):
    __tablename__ = "Gig_Listings"

    gig_id = Column(Integer, primary_key=True, autoincrement=True)
    venue_owner_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    gig_title = Column(String(200), nullable=False)
    description = Column(Text)
    genre_required = Column(String(100), nullable=False)
    performance_date = Column(Date, nullable=False)
    performance_time = Column(Time, nullable=False)
    venue_name = Column(String(150), nullable=False)
    location_city = Column(String(100), nullable=False)
    location_zip_code = Column(String(10))
    duration_hours = Column(Numeric(3, 1))
    offered_pay = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(String(20), default="Pending")
    gig_status = Column(SAEnum(GigStatus, native_enum=False), default=GigStatus.OPEN)
    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    venue_owner = relationship("User", back_populates="gig_listings")
    applications = relationship("Application", back_populates="gig")
    bookings = relationship("BookingContract", back_populates="gig")
    setlists = relationship("Setlist", back_populates="gig")


class Application(Base):
    __tablename__ = "Applications"

    application_id = Column(Integer, primary_key=True, autoincrement=True)
    gig_id = Column(Integer, ForeignKey("Gig_Listings.gig_id", ondelete="CASCADE"), nullable=False)
    band_id = Column(Integer, ForeignKey("Bands.band_id", ondelete="CASCADE"), nullable=False)
    application_date = Column(DateTime, server_default=func.now())
    application_status = Column(SAEnum(ApplicationStatus, native_enum=False), default=ApplicationStatus.PENDING)
    cover_letter = Column(Text)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    gig = relationship("GigListing", back_populates="applications")
    band = relationship("Band", back_populates="applications")


class BookingContract(Base):
    __tablename__ = "Bookings_Contracts"

    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    gig_id = Column(Integer, ForeignKey("Gig_Listings.gig_id", ondelete="CASCADE"), nullable=False)
    band_id = Column(Integer, ForeignKey("Bands.band_id", ondelete="CASCADE"), nullable=False)
    venue_owner_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    contract_date = Column(DateTime, server_default=func.now())
    agreed_fee = Column(Numeric(10, 2), nullable=False)
    deposit_amount = Column(Numeric(10, 2))
    deposit_status = Column(SAEnum(DepositStatus, native_enum=False), default=DepositStatus.PENDING)
    contract_status = Column(SAEnum(BookingStatus, native_enum=False), default=BookingStatus.ACTIVE)
    performance_date = Column(Date, nullable=False)
    performance_time = Column(Time, nullable=False)
    contract_terms = Column(Text)
    signed_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    gig = relationship("GigListing", back_populates="bookings")
    band = relationship("Band", back_populates="bookings")
    venue_owner = relationship("User", back_populates="bookings_as_venue")
    payments = relationship("Payment", back_populates="booking")
    reviews = relationship("ReviewDispute", back_populates="booking")


class AvailabilityCalendar(Base):
    __tablename__ = "Availability_Calendar"

    availability_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    busy_date = Column(Date, nullable=False)
    busy_time_start = Column(Time)
    busy_time_end = Column(Time)
    reason = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "busy_date"),
    )

    user = relationship("User", back_populates="availability")


class Payment(Base):
    __tablename__ = "Payments"

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("Bookings_Contracts.booking_id", ondelete="CASCADE"), nullable=False)
    band_id = Column(Integer, ForeignKey("Bands.band_id", ondelete="CASCADE"), nullable=False)
    venue_owner_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_type = Column(String(20), nullable=False)  # 'Deposit', 'Final'
    payment_status = Column(SAEnum(PaymentStatus, native_enum=False), default=PaymentStatus.PENDING)
    payment_date = Column(DateTime)
    payment_method = Column(String(50))
    transaction_id = Column(String(100), unique=True)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    booking = relationship("BookingContract", back_populates="payments")
    band = relationship("Band", back_populates="payments")
    venue_owner = relationship("User", back_populates="payments_as_venue")


class RecruitmentAd(Base):
    __tablename__ = "Recruitment_Ads"

    recruitment_id = Column(Integer, primary_key=True, autoincrement=True)
    band_id = Column(Integer, ForeignKey("Bands.band_id", ondelete="CASCADE"), nullable=False)
    posted_by_user_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    instruments_needed = Column(String(255), nullable=False)
    genre = Column(String(100), nullable=False)
    experience_level = Column(SAEnum(ExperienceLevel, native_enum=False))
    city = Column(String(100))
    zip_code = Column(String(10))
    ad_status = Column(SAEnum(AdStatus, native_enum=False), default=AdStatus.ACTIVE)
    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    band = relationship("Band", back_populates="recruitment_ads")
    posted_by = relationship("User", back_populates="recruitment_ads_posted")


class ReviewDispute(Base):
    __tablename__ = "Reviews_Disputes"

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("Bookings_Contracts.booking_id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    reviewee_id = Column(Integer, ForeignKey("Users.user_id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer)
    review_text = Column(Text)
    review_type = Column(SAEnum(ReviewType, native_enum=False), default=ReviewType.REVIEW)
    dispute_reason = Column(String(255))
    is_flagged = Column(Boolean, default=False)
    admin_notes = Column(Text)
    status = Column(SAEnum(ReviewStatus, native_enum=False), default=ReviewStatus.OPEN)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime)

    booking = relationship("BookingContract", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewee = relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")


class Setlist(Base):
    __tablename__ = "Setlists"

    setlist_id = Column(Integer, primary_key=True, autoincrement=True)
    band_id = Column(Integer, ForeignKey("Bands.band_id", ondelete="CASCADE"), nullable=False)
    gig_id = Column(Integer, ForeignKey("Gig_Listings.gig_id", ondelete="SET NULL"))
    setlist_name = Column(String(200), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    band = relationship("Band", back_populates="setlists")
    gig = relationship("GigListing", back_populates="setlists")
    songs = relationship("SetlistSong", back_populates="setlist")


class SetlistSong(Base):
    __tablename__ = "Setlist_Songs"

    song_id = Column(Integer, primary_key=True, autoincrement=True)
    setlist_id = Column(Integer, ForeignKey("Setlists.setlist_id", ondelete="CASCADE"), nullable=False)
    song_title = Column(String(200), nullable=False)
    artist_name = Column(String(150))
    duration_minutes = Column(Numeric(4, 2))
    song_order = Column(Integer, nullable=False)
    genre = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

    setlist = relationship("Setlist", back_populates="songs")

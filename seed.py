import datetime
from auth import hash_password
from database import get_db, init_db
from models import GigListing, GigStatus, User, UserRole

def seed_demo_data() -> None:
    init_db()
    with get_db() as db:
        if db.query(User).filter(User.username == "seniya").first():
            print("Demo data already exists."); return
        client = User(username="seniya", email="seniya@example.com", password_hash=hash_password("seniya"), first_name="Seniya", last_name="Owner", role=UserRole.VENUE_OWNER, city="Karachi", is_active=True)
        musician = User(username="lucky", email="lucky@example.com", password_hash=hash_password("lucky123"), first_name="Lucky", last_name="Musician", role=UserRole.MUSICIAN, city="Karachi", bio="Session guitarist and vocalist available for live shows.", is_active=True)
        db.add_all([client, musician]); db.flush()
        today = datetime.date.today()
        db.add_all([
            GigListing(venue_owner_id=client.user_id, gig_title="Friday Jazz Night", description="Need a smooth jazz performer for a dinner crowd.", genre_required="Jazz", location_city="Karachi", performance_date=today + datetime.timedelta(days=10), performance_time=datetime.time(20, 0), duration_hours=3, offered_pay=500, gig_status=GigStatus.OPEN),
            GigListing(venue_owner_id=client.user_id, gig_title="Acoustic Rooftop Set", description="Chill acoustic set for a private event.", genre_required="Folk", location_city="Karachi", performance_date=today + datetime.timedelta(days=18), performance_time=datetime.time(19, 0), duration_hours=2, offered_pay=350, gig_status=GigStatus.OPEN),
        ])
        print("Demo data seeded. Login: seniya / seniya or lucky / lucky123")

if __name__ == "__main__": seed_demo_data()

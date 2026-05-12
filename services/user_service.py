from database import get_db
from models import User


def get_user_by_id(user_id: int) -> User | None:
    with get_db() as db:
        return (
            db.query(User)
            .filter(User.user_id == user_id, User.is_active == True)
            .first()
        )


def update_user_profile(
    user_id: int,
    bio: str,
    city: str,
) -> User:
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError("User not found.")

        user.bio = bio
        user.city = city

        db.commit()
        db.refresh(user)
        return user


def update_user_bio(user_id: int, bio: str) -> None:
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.bio = bio
            db.commit()

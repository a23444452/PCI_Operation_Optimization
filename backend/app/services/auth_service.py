import secrets

from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import hash_password, verify_password

_AD_USER_SENTINEL_PREFIX = "!AD_ONLY!"


def _unusable_password_hash() -> str:
    return f"{_AD_USER_SENTINEL_PREFIX}{secrets.token_urlsafe(32)}"


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user is None or not verify_password(password, user.password_hash):
        return None
    if user.status != "active":
        return None
    return user

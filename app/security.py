from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_hasher = PasswordHasher()

MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def password_error(password: str, username: str | None = None, email: str | None = None) -> str | None:
    """Return an error message when the password is unacceptable, else None."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    check = (username or "").lower()
    if not check and email:
        check = (email or "").split("@")[0].lower()
    if check and password.lower() == check:
        return "Password must not equal the username."
    return None

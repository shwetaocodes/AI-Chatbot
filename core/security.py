from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plain text password. Returns a bcrypt hash string."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain text password against a bcrypt hash.
    Uses timing-safe comparison — never use == for this."""
    return pwd_context.verify(plain, hashed)
import hashlib
import hmac
import secrets
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

HASHER = PasswordHasher()


def hash_password(password: str) -> str:
    return HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return HASHER.verify(password_hash, password)
    except VerificationError:
        return False


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def new_token() -> str:
    return secrets.token_urlsafe(32)


def new_secret_bytes(size: int = 32) -> bytes:
    return secrets.token_bytes(size)


def new_key() -> str:
    return uuid4().hex


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode(), right.encode())


def make_import_token(secret: bytes, user_id: int, token_hash: str, encoded_payload: str) -> str:
    message = f'{user_id}:{token_hash}:{encoded_payload}'
    return hmac.new(secret, message.encode(), hashlib.sha256).hexdigest()

import base64
import binascii
import hashlib
import hmac
import time
import os


SECRET_KEY = os.getenv("SECRET", "")

def make_token(telegram_id: int, ttl_seconds: int = 3600) -> str:
    expires_at = int(time.time()) + ttl_seconds
    payload = f"{telegram_id}:{expires_at}"
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    raw = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def verify_token(token: str) -> int:
    if not token:
        raise ValueError("Geçersiz token")

    try:
        padding = "=" * (-len(token) % 4)
        raw_bytes = base64.urlsafe_b64decode((token + padding).encode("ascii"))
        raw = raw_bytes.decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise ValueError("Geçersiz token formatı")

    try:
        telegram_id_str, expires_at_str, signature = raw.rsplit(":", 2)
    except ValueError:
        raise ValueError("Geçersiz token formatı")

    payload = f"{telegram_id_str}:{expires_at_str}"
    expected_signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Geçersiz token")

    try:
        expires_at = int(expires_at_str)
        telegram_id = int(telegram_id_str)
    except ValueError:
        raise ValueError("Geçersiz token formatı")

    if expires_at < int(time.time()):
        raise ValueError("Token süresi dolmuş")

    return telegram_id
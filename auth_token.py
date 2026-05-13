import os
import time
from jose import JWTError, jwt

# Çevresel değişkenden SECRET_KEY alımı
SECRET_KEY = os.getenv("SECRET", "varsayilan_gizli_anahtar")
ALGORITHM = "HS256"


def make_token(telegram_id: int, ttl_seconds: int = 3600) -> str:
    """
    Kullanıcı ID'sini ve son kullanma tarihini içeren bir JWT üretir.
    """
    expire = int(time.time()) + ttl_seconds
    to_encode = {
        "sub": str(telegram_id),  # 'sub' (subject) standart bir JWT alanıdır
        "exp": expire             # 'exp' (expiration) otomatik kontrol edilir
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> int:
    """
    Token'ı doğrular, süresini kontrol eder ve telegram_id döner.
    """
    if not token:
        raise ValueError("Geçersiz token")

    try:
        # jose kütüphanesi imzayı ve 'exp' süresini otomatik kontrol eder
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        telegram_id = payload.get("sub")

        if telegram_id is None:
            raise ValueError("Token içeriği eksik")

        return int(telegram_id)

    except JWTError:
        # İmza hatalıysa veya süre dolmuşsa jose JWTError fırlatır
        raise ValueError("Geçersiz veya süresi dolmuş token")
    except ValueError:
        raise ValueError("Geçersiz veri formatı")


def admin_make_token(token: str, ttl_seconds: int = 3600):
    """
    Kullanıcı ID'sini ve son kullanma tarihini içeren bir JWT üretir.
    """
    expire = int(time.time()) + ttl_seconds
    to_encode = {
        "sub": str(token),  # 'sub' (subject) standart bir JWT alanıdır
        "exp": expire             # 'exp' (expiration) otomatik kontrol edilir
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def admin_verify_token(token: str):
    """
    Token'ı doğrular, süresini kontrol eder ve telegram_id döner.
    """
    if not token:
        raise ValueError("Geçersiz token")

    try:
        # jose kütüphanesi imzayı ve 'exp' süresini otomatik kontrol eder
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        telegram_token = payload.get("sub")

        if telegram_token is None:
            raise ValueError("Token içeriği eksik")
        telegram_id = verify_token(telegram_token)

        return int(telegram_id)

    except JWTError:
        # İmza hatalıysa veya süre dolmuşsa jose JWTError fırlatır
        raise ValueError("Geçersiz veya süresi dolmuş token")
    except ValueError:
        raise ValueError("Geçersiz veri formatı")

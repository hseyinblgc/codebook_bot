import os
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from auth_token import verify_token
from database import insertdb

app = FastAPI()

admin_id = os.getenv("ADMIN_ID")
# IP Limit
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
        request: Request, exc: RateLimitExceeded):

    if request.url.path == "/verify-token":
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Doğrulama sınırına ulaşıldı."
                " Biraz sonra tekrar deneyin."
                }
        )

    return JSONResponse(
        status_code=429,
        content={
            "detail": "Çok fazla istek. Lütfen daha sonra tekrar deneyin."}
    )


# Veriyi doğrula (başvuru)
class Basvuru(BaseModel):
    token: str = Field(..., min_length=10)
    ad_soyad: str = Field(..., min_length=2, max_length=100)
    github_user: str = Field(..., min_length=1, max_length=39)
    proje_adi: str = Field(..., min_length=1, max_length=200)
    proje_ozet: str = Field(..., min_length=10, max_length=5000)
    onay: bool


# Veriyi doğrula (verify-token)
class TokenPayload(BaseModel):
    token: str = Field(..., min_length=10)


@app.post("/basvuru")
@limiter.limit("3/minute")
async def basvuru_al(request: Request,
                     data: Basvuru,
                     background_tasks: BackgroundTasks):
    try:
        telegram_id = verify_token(data.token)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Geçersiz veya süresi dolmuş bağlantı.")

    values = (
        telegram_id,
        data.ad_soyad,
        data.github_user,
        data.proje_adi,
        data.proje_ozet,
        "pending",
    )
    insertdb(values)

    return {
        "ok": True,
        "mesaj": "Başvuru alındı. Admin onayı bekleniyor. "
        "Sayfayı kapatabilirsiniz"
    }


@app.post("/verify-token")
@limiter.limit("3/minute")
async def verify_token_endpoint(request: Request, payload: TokenPayload):
    try:
        verify_token(payload.token)
    except ValueError:
        raise HTTPException(status_code=400,
                            detail="Geçersiz veya süresi dolmuş bağlantı.")
    return {"ok": True}


@app.post("/admin-auth")
@limiter.limit("20/minute")
async def verify_admin(request: Request, payload: TokenPayload):
    try:
        telegram_id = verify_token(payload.token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Admin ID doğrula
    if str(telegram_id) != str(admin_id):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"ok": True}

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apply_bot import Admin, send_user_message
from auth_token import verify_token
import os


admin_token = os.getenv("ADMIN_TOKEN", "")
user_token = os.getenv("USER_TOKEN", "")
admin_id_raw = os.getenv("ADMIN_ID", "")
admin_id = int(admin_id_raw)
admin_service = Admin(
    admin_token=admin_token,
    user_token=user_token,
    chat_id=admin_id
)

app = FastAPI()

# IP Limit
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    if request.url.path == "/verify-token":
        return JSONResponse(
            status_code=429,
            content={"detail": "Doğrulama sınırına ulaşıldı. Biraz sonra tekrar deneyin."}
        )

    return JSONResponse(
        status_code=429,
        content={"detail": "Çok fazla istek. Lütfen daha sonra tekrar deneyin."}
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


# Admin onay mesajı (Mesaj içeriği)
def build_admin_message(data: Basvuru) -> str:
    return (
        f"Proje adı: {data.proje_adi}\n\n"
        f"Açıklama: {data.proje_ozet}\n\n"
        f"Kimden: {data.ad_soyad}\n\n"
        f"GitHub: {data.github_user}"
    )

# Admin onay mesajı
async def run_admin_flow(data: Basvuru, telegram_id: int):
    message_text = "Yeni başvuru geldi. Onaylıyor musunuz?\n\n" + build_admin_message(data)
    result = await admin_service.request_admin_decision(
        message_text,
        timeout_seconds=300,
    )

    status = result["status"]
    reason = result["reason"]
    summary = build_admin_message(data)

    if status == "approved":
        message = "Tebrikler! Projeniz onaylandı.\n" + summary
    else:
        message = (
            f"Projeniz reddedildi.\n"
            f"{summary}\n\n"
            f"Red sebebi:\n {reason}"
        )

    await send_user_message(text=message, user_id=telegram_id)


@app.post("/basvuru")
@limiter.limit("3/minute")
async def basvuru_al(request: Request, data: Basvuru, background_tasks: BackgroundTasks):
    try:
        telegram_id = verify_token(data.token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş bağlantı.")

    background_tasks.add_task(run_admin_flow, data, telegram_id)
    return {
        "ok": True,
        "mesaj": "Başvuru alındı. Admin onayı bekleniyor. Sayfayı kapatabilirsiniz"
    }



@app.post("/verify-token")
@limiter.limit("3/minute")
async def verify_token_endpoint(request: Request, payload: TokenPayload):
    try:
        verify_token(payload.token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş bağlantı.")
    return {"ok": True}


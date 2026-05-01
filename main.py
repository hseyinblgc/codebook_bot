from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field  # Field buradan gelsin
from basvuru_bot import Admin, send_user_message
from config import admin_token, user_token, admin_id

admin_service = Admin(
    admin_token=admin_token,
    user_token=user_token,
    chat_id=admin_id
)

app = FastAPI()


class Basvuru(BaseModel):
    telegram_id: int = Field(..., gt=0, le=9999999999)
    ad_soyad: str = Field(..., min_length=2, max_length=100)
    github_user: str = Field(..., pattern=r'^[a-zA-Z0-9-]{1,39}$')
    proje_adi: str = Field(..., min_length=1, max_length=200)
    proje_ozet: str = Field(..., min_length=10, max_length=5000)
    onay: bool




def build_admin_message(data: Basvuru) -> str:
    return (
        f"Proje adı: {data.proje_adi}\n\n"
        f"Açıklama: {data.proje_ozet}\n\n"
        f"Kimden: {data.ad_soyad}\n\n"
        f"GitHub: {data.github_user}"
    )

async def run_admin_flow(data: Basvuru):
    message_text ="Yeni başvuru geldi. Onaylıyor musunuz?\n\n" + build_admin_message(data)
    result = await admin_service.request_admin_decision(
        message_text,
        timeout_seconds=300,
    )

    status = result["status"]
    reason = result["reason"]
    summary = build_admin_message(data)

    if status == "approved":
        message = ("Tebrikler! Projeniz onaylandı. \n"
                  f"{summary}")
    else:
        message = (
        f"Projeniz reddedildi.\n"
        f"{summary}\n\n"
        f"Red sebebi:\n {reason}")
    await send_user_message(text=message, user_id=data.telegram_id)


@app.post("/basvuru")
async def basvuru_al(data: Basvuru, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_admin_flow, data)
    return {
        "ok": True,
        "mesaj": "Başvuru alındı. Admin onayı bekleniyor. Sayfayı kapatabilirsiniz"
    }



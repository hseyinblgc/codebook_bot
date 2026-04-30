from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from basvuru_bot import Admin, send_user_message
from config import admin_token, user_token, admin_id

admin_service = Admin(
    admin_token=admin_token,
    user_token=user_token,
    chat_id=admin_id
)

app = FastAPI()


class Basvuru(BaseModel):
    ad_soyad: str
    github_user: str
    proje_adi: str
    proje_ozet: str
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
    await send_user_message(text=message)


@app.post("/basvuru")
async def basvuru_al(data: Basvuru, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_admin_flow, data)
    return {
        "ok": True,
        "mesaj": "Başvuru alındı. Admin onayı bekleniyor. Sayfayı kapatabilirsiniz"
    }



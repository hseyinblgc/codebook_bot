import streamlit as st
import requests
from config import API

API_URL = API + "/basvuru"
API_VERIFY = API + "/verify-token"

token = st.query_params.get("token")

st.set_page_config(page_title="Proje Kayıt Formu", layout="centered")

st.title("Açık Kaynak Proje Başvuru Formu")

if not token:
    st.error("Geçersiz veya eksik bağlantı.")
    st.stop()

# Sunucuya doğrulama isteği at
try:
    v = requests.post(API_VERIFY, json={"token": token}, timeout=5)
    v.raise_for_status()
except requests.HTTPError as e:
    # sunucu 400 ise kullanıcıya temiz mesaj göster
    detail = None
    if getattr(e, "response", None) is not None:
        try:
            detail = e.response.json().get("detail")
        except Exception:
            detail = e.response.text
    st.error("Geçersiz veya süresi dolmuş bağlantı.")
    st.stop()
except requests.RequestException:
    st.error("Doğrulama sunucusuna ulaşılamıyor. Lütfen daha sonra deneyin.")
    st.stop()

# doğrulandı → formu göster (mevcut kod devam eder)

with st.form("proje_formu", clear_on_submit=False):
    ad_soyad = st.text_input("Adınız ve Soyadınız")
    github_user = st.text_input("GitHub Kullanıcı Adınız")
    proje_adi = st.text_input("Proje Adı")
    proje_ozet = st.text_area("Projenizden kısaca bahsedin")
    onay = st.checkbox("Yukarıdaki şartları kabul ediyorum.")
    submit_button = st.form_submit_button("Başvuruyu Tamamla")

if submit_button:
    if not ad_soyad or not github_user or not proje_adi or not proje_ozet:
        st.error("Lütfen tüm alanları doldurun.")
    elif not onay:
        st.warning("Devam etmek için onay vermelisiniz.")
    else:
        payload = {
            "token": token,
            "ad_soyad": ad_soyad,
            "github_user": github_user,
            "proje_adi": proje_adi,
            "proje_ozet": proje_ozet,
            "onay": onay
        }

        try:
            resp = requests.post(API_URL, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            st.success(data.get("mesaj", "Başvuru alındı."))
        except requests.HTTPError as e:
            resp = getattr(e, "response", None)
            if resp is not None and resp.status_code == 429:
                try:
                    detail = resp.json().get("detail")
                except Exception:
                    detail = None
                st.error(detail or "Çok fazla istek. Lütfen daha sonra tekrar deneyin.")
            else:
                st.error(f"Gönderim hatası: {str(e)}")
        except requests.RequestException as e:
            st.error(f"Gönderim hatası: {e}")

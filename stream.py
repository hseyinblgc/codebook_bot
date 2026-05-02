import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/basvuru"

token = st.query_params.get("token")

st.set_page_config(page_title="Proje Kayıt Formu", layout="centered")

st.title("Açık Kaynak Proje Başvuru Formu")

if not token:
    st.error("Geçersiz veya eksik bağlantı.")
    st.stop()

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

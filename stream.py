import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/basvuru"

# Sayfa Başlığı
st.set_page_config(page_title="Proje Kayıt Formu", layout="centered")

st.title("🚀 Açık Kaynak Proje Başvuru Formu")
st.write(
    "Lütfen aşağıdaki bilgileri eksiksiz doldurunuz. Tüm alanlar zorunludur."
    )

# Form Başlangıcı
with st.form("proje_formu", clear_on_submit=False):
    # Kullanıcı Bilgileri
    ad_soyad = st.text_input("Adınız ve Soyadınız")
    github_user = st.text_input("GitHub Kullanıcı Adınız (Örn: username)")

    # Proje Bilgileri
    proje_adi = st.text_input("Proje Adı")
    proje_ozet = st.text_area(
        "Projenizden kısaca bahsedin (Birkaç cümle)",
        help="Projenin amacını ve ne yaptığını açıklayın.")

    # Lisans Metni ve Onay Kutusu
    st.markdown("### ⚖️ Lisans ve Kullanım Şartları")
    lisans_metni = """
    Bu proje tamamen açık kaynaklı olacak ve otomatik olarak **AGPLv3 Lisansıyla** lisanslanacak. 
    Kısaca kamuya ait olacak. Bu proje benim diyerek sana yardım eden kullanıcıların emeğini çalamaz, 
    kendine saklayamazsın. Ayrıca kendi kişisel işini başkasına yaptırıp üzerinden maddiyat elde edemezsin. 
    Kişisel işini başkasına yaptıramazsın. Bu proje OpenSource topluluğuna ait olacak.
    """
    st.info(lisans_metni)

    onay = st.checkbox(
        "Yukarıdaki şartları ve lisans anlaşmasını kabul ediyorum.")

    # Gönder Butonu
    submit_button = st.form_submit_button("Başvuruyu Tamamla")

# Form Gönderildiğinde Yapılacak Kontroller
if submit_button:
    # Zorunlu alan kontrolü
    if not ad_soyad or not github_user or not proje_adi or not proje_ozet:
        st.error("Lütfen tüm metin alanlarını doldurduğunuzdan emin olun!")
    elif not onay:
        st.warning(
            "Devam etmek için lisans anlaşmasını onaylamanız gerekmektedir.")
    else:
        # Başarılı kayıt durumunda yapılacak işlemler
        st.success(
            f"Teşekkürler {ad_soyad}! Projeniz '{proje_adi}'"
            "başarıyla kaydedildi.")

        # Verileri ekrana yazdırma (veya bir veritabanına gönderme)
        st.balloons()
        payload = {
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
            st.success(data.get("mesaj", "Mesaj bulunamadi"))
        except requests.RequestException as e:
            st.error(f"Gonderim hatasi: {e}")

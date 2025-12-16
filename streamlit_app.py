# streamlit_app.py
# Araç İçi Sosyal Uyum Anketi — Google Cloud'suz Kalıcı Kayıt
# - 5'li Likert
# - AHP için basit ikili karşılaştırma girişleri (önemli taraf + 1–9 katsayı)
# - Yerel CSV'ye ve (opsiyonel) Google Apps Script Web App'e kayıt

import streamlit as st
import pandas as pd
import os, json, requests
from datetime import datetime

# --- GÖMÜLÜ AYARLAR ---
USE_APPS_SCRIPT = True  # True ise Sheets'e de gönderir
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxom9lOJI1PT4dsKchrTCi-v25SdJODylfNCSOD41ctT7F16s7OgOnK0HWq_LXaOavLOQ/exec"
SEND_AS_JSON = True     # JSON gönder (önerilir)

st.set_page_config(page_title="Araç İçi Sosyal Uyum Anketi", page_icon="🧭", layout="wide")
st.title("Araç İçi Sosyal Uyum Anketi")
st.caption("📝 Bu form, birlikte seyahat edecek kişilerin sosyal uyum tercihlerini anlamaya yöneliktir.")

with st.expander("📌 Anket Hakkında Bilgilendirme", expanded=True):
    st.markdown(
        """
Sayın katılımcılar, bu anket, araç içinde birlikte seyahat edecek kişilerin sosyal uyumunu daha iyi anlamak ve
uygun gruplar oluşturabilmek amacıyla yürütülen **bilimsel bir projeye** veri toplamak amacıyla
hazırlanmıştır. Anket formunda kimlik bilgileri ve çalışılan kurum
bilgilerine kesinlikle ihtiyaç yoktur. Katılımcılardan alınacak bilgiler yalnızca
araştırma kapsamında kullanılacak, üçüncü kişilerle paylaşılmayacaktır. Anket formunda yer alan
sorular; sigara kullanımı, cinsiyet tercihi, medeni hâl, eğitim düzeyi, çalışan seviyesi, yaş/nesil,
müzik veya sessizlik tercihi gibi araç içi uyuma etki edebilecek kriterlere yöneliktir. Katkınız için teşekkür ederiz.
        """
    )

st.markdown("---")

# ======= Stil (yalnızca Likert alanına uygulanır) =======
st.markdown("""
<style>
.center { text-align: center; }

/* —— Likert hizası (masaüstü) —— */
#likert-scope div[role="radiogroup"]{
  gap: 2.2rem;              /* daireler arası */
}
#likert-scope div[role="radiogroup"] > label{
  min-width: 70px;          /* her dairenin kutusu */
  display: inline-flex;
  justify-content: center;
  align-items: center;
}
/* Radio metinlerini gizle (sadece daire kalsın) */
#likert-scope div[role="radiogroup"] > label span{
  font-size: 0 !important; line-height: 0;
}

/* —— Satır ayırıcı: ince gri çizgi —— */
.likert-sep { margin: .30rem 0 .40rem 0; border: 0; border-top: .5px solid #ddd; }

/* —— Mobil optimizasyon —— */
@media (max-width: 640px){
  #likert-scope .center{ font-size: .9rem; }
  #likert-scope div[role="radiogroup"]{ gap: .9rem; }
  #likert-scope div[role="radiogroup"] > label{ min-width: 36px; }
  .stButton > button { width: 100%; }
}
</style>
""", unsafe_allow_html=True)

# ======= Sabitler =======
RESP_PATH = "../../Downloads/arac_ici_sosyal_uyum_anketi_apps_script/responses.csv"
LIKERT_OPTIONS = ["Kesinlikle Katılıyorum","Katılıyorum","Kararsızım","Katılmıyorum","Kesinlikle Katılmıyorum"]
LIKERT_MAP = {"Kesinlikle Katılıyorum":5, "Katılıyorum":4, "Kararsızım":3, "Katılmıyorum":2, "Kesinlikle Katılmıyorum":1}

AHP_CRITERIA = [
    "Cinsiyet",
    "Medeni hâl",
    "Yaş / nesil",
    "Eğitim seviyesi",
    "Çalışan pozisyonu / meslek düzeyi",
    "Sigara kullanımı",
    "Müzik tercihleri",
    "Dakiklik",
    "Sessizlik tercihi",
]

# ======= Form =======
st.subheader("1) Kişisel Bilgiler")
with st.form("survey_form"):
    # --- Kişisel bilgiler ---
    c1, c2, c3 = st.columns(3)
    with c1:
        gender = st.radio("Cinsiyetiniz", ["Kadın", "Erkek"], horizontal=True)
        marital = st.radio("Medeni hâliniz", ["Evli", "Bekâr"], horizontal=True)
        smoking = st.radio("Sigara kullanımı", ["Evet", "Hayır"], horizontal=True)
    with c2:
        age = st.selectbox("Yaş aralığınız", ["18–29", "30–44", "45–59", "60+"])
        edu = st.selectbox("Eğitim durumunuz", ["İlkokul", "Ortaokul", "Lise", "Ön Lisans", "Lisans", "Yüksek Lisans", "Doktora"])
        position = st.selectbox("Çalışan pozisyonunuz", ["Stajyer","Saha Personeli","Ofis Görevlisi","İdari Personel" ,"Yeni Mezun / Junior", "Orta Düzey", "Kıdemli", "Takım Lideri", "Yönetici", "Üst Yönetim"])
    with c3:
        music = st.multiselect(
            "Araç içinde dinlemekten hoşlandığınız müzik tür(ler)i (çoklu seçim yapabilirsiniz)",
            ["Pop", "Rock", "Caz", "Klasik", "Rap / Hip Hop", "Elektronik / Dance",
             "Türk Halk Müziği", "Türk Sanat Müziği", "Arabesk", "Blues / Soul"]
        )

    st.markdown("---")

    c4, c5 = st.columns(2)
    with c4:
        punctuality_opt = st.radio(
            "Randevu ve yolculuklara geç kalma durumum sık yaşanır.",
            LIKERT_OPTIONS,
            index=2,
            horizontal=False
        )

    with c5:
        silence_opt = st.radio(
            "Yolculuk sırasında genellikle sessiz kalmayı tercih ederim.",
            LIKERT_OPTIONS,
            index=2,
            horizontal=False
        )

    st.markdown("---")
    # --- Likert ---
    st.subheader("2) Yol Arkadaşı Tercihleriniz")
    st.caption("Her ifadenin size ne kadar uyduğunu işaretleyiniz.")
    st.markdown('<div id="likert-scope">', unsafe_allow_html=True)

    likert_prompts = [
        "Araç içinde birlikte seyahat edeceğim kişilerin **aynı cinsiyette** olmasını tercih ederim.",
        "Araç içinde birlikte seyahat edeceğim kişilerin **benzer yaş aralığında/kuşağında** olmasını tercih ederim.",
        "Araç içinde birlikte seyahat edeceğim kişilerin **benzer medeni hâlde** olmasını tercih ederim.",
        "Araç içinde birlikte seyahat edeceğim kişilerin **benzer eğitim seviyesinde** olmasını tercih ederim.",
        "Araç içinde birlikte seyahat edeceğim kişilerin **benzer meslek/çalışan düzeyinde** olmasını tercih ederim.",
        "Araç içinde birlikte seyahat edeceğim kişilerin **sigara kullanmıyor** olmasını tercih ederim.",
        "Araç içinde birlikte seyahat edeceğim kişilerin **benzer müzik zevkine** sahip olmasını tercih ederim.",
    ]

    likert_answers = {}
    for i, q in enumerate(likert_prompts, start=1):
        st.markdown(
            "<div style='background-color:#f0f0f0; padding:0.22rem 0.5rem; border-radius:6px;'>",
            unsafe_allow_html=True
        )
        cols = st.columns([4.8, 5.2])
        with cols[0]:
            st.markdown(q)
        with cols[1]:
            sel = st.radio(
                f"_row_{i}", LIKERT_OPTIONS, index=2, horizontal=True,
                label_visibility="collapsed", key=f"likert_{i}"
            )
            likert_answers[f"Q{i}_opt"] = sel
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<hr class='likert-sep'>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # --- AHP: kriterlerin ikili karşılaştırması (slider) ---
    st.markdown("---")
    st.subheader("3) Kriterleri Kıyaslayın ve Önem Derecesini Seçin")

    st.caption(
        "Her satırda iki kriteri karşılaştırın. Kaydırma çubuğuyla hem hangisinin daha önemli olduğunu "
        "hem de ne kadar daha önemli olduğunu seçin.\n"
        "- Ortadaki **1**: İki kriter eşit derecede önemli\n"
        "- Solda **2–9**: Sol kriter daha önemli (sayı büyüdükçe fark artar)\n"
        "- Sağda **2–9**: Sağ kriter daha önemli (sayı büyüdükçe fark artar)"
    )

    pairwise_entries = []
    display_values = ["9L","8L","7L","6L","5L","4L","3L","2L","1","2R","3R","4R","5R","6R","7R","8R","9R"]
    labels = ["9","8","7","6","5","4","3","2","1","2","3","4","5","6","7","8","9"]

    n = len(AHP_CRITERIA)
    for i in range(n):
        for j in range(i+1, n):
            left = AHP_CRITERIA[i]
            right = AHP_CRITERIA[j]

            st.markdown(
                "<div style='padding:0.4rem 0.6rem; border-radius:6px; "
                "border:1px solid #eee; margin-bottom:0.6rem;'>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**{left}** ile **{right}** arasında önem karşılaştırması:", unsafe_allow_html=True)

            c_left, c_slider, c_right = st.columns([1.5, 6, 1.5])
            with c_left:
                st.markdown(f"<div style='text-align:left; font-weight:600;'>{left}</div>", unsafe_allow_html=True)

            with c_slider:
                selected = st.select_slider(
                    f"ahp_{i}_{j}",
                    options=display_values,
                    value="1",
                    format_func=lambda x: labels[display_values.index(x)],
                    key=f"ahp_{i}_{j}",
                    label_visibility="collapsed",
                )

                numbers_html = "<div style='display:flex; justify-content:space-between; " \
                               "font-size:0.75rem; color:#666; margin-top:2px;'>"
                for lab in labels:
                    numbers_html += f"<span style='flex:1; text-align:center;'>{lab}</span>"
                numbers_html += "</div>"
                st.markdown(numbers_html, unsafe_allow_html=True)

            with c_right:
                st.markdown(f"<div style='text-align:right; font-weight:600;'>{right}</div>", unsafe_allow_html=True)

            if selected == "1":
                preferred = "Eşit"
                ratio = 1
            elif selected.endswith("L"):
                preferred = left
                ratio = int(selected[:-1])
            else:
                preferred = right
                ratio = int(selected[:-1])

            st.markdown("</div>", unsafe_allow_html=True)

            pairwise_entries.append({
                "left": left,
                "right": right,
                "raw_value": selected,
                "preferred": preferred,
                "ratio": ratio,
            })

    st.markdown("---")
    consent = st.checkbox("Gönüllü olarak katılıyorum ve verdiğim bilgilerin araştırma kapsamında kullanılmasını onaylıyorum.")
    submitted = st.form_submit_button("Gönder", use_container_width=True, type="primary")


# ======= Gönderim =======
if submitted:
    if not consent:
        st.error("Lütfen katılım onay kutusunu işaretleyiniz.")
    else:
        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "gender": gender,
            "marital": marital,
            "age_range": age,
            "education": edu,
            "position": position,
            "smoking": smoking,
            "music": "; ".join(music) if music else "",

            # ✅ YENİ: Dakiklik ve sessizlik
            "punctuality_late": int(LIKERT_MAP[punctuality_opt]),                 # 5 = sık geç kalma
            "punctuality_score": 6 - int(LIKERT_MAP[punctuality_opt]),           # 5 = çok dakik
            "punctuality_label": punctuality_opt,

            "silence": int(LIKERT_MAP[silence_opt]),                             # 5 = daha sessiz
            "silence_label": silence_opt,
        }

        # Likert kayıtları
        for i in range(1, 8):
            opt = likert_answers[f"Q{i}_opt"]
            row[f"Q{i}"] = int(LIKERT_MAP[opt])
            row[f"Q{i}_label"] = opt

        # AHP basit girişlerini JSON olarak ekle
        row["ahp_pairwise_json"] = json.dumps(pairwise_entries, ensure_ascii=False)


        # 2) Google Apps Script Web App
        if USE_APPS_SCRIPT and WEB_APP_URL.strip() != "":
            try:
                payload = row.copy()
                if SEND_AS_JSON:
                    headers = {"Content-Type": "application/json"}
                    r = requests.post(WEB_APP_URL, headers=headers, data=json.dumps(payload), timeout=10)
                else:
                    r = requests.post(WEB_APP_URL, data=payload, timeout=10)
                if r.status_code == 200:
                    st.success("Yanıtlarınız kaydedildi. Katılımınız için teşekkürler.")
                else:
                    st.warning(f"Web App cevap kodu: {r.status_code}. Detay: {r.text[:200]}")
            except Exception as e:
                st.error(f"Yanıtlarınız kaydedilemedi!: {e}")



st.markdown("---")

# streamlit_app.py
# Araç İçi Sosyal Uyum Anketi — Yeni AHP Soruları
import streamlit as st
import pandas as pd
import os, json, requests
from datetime import datetime
import numpy as np
def calc_ahp_cr(matrix):
    """3x3 AHP matrisi için Tutarlılık Oranı (CR) hesaplar."""
    n = matrix.shape[0]
    # Sütun toplamlarına bölerek normalize et
    col_sums = matrix.sum(axis=0)
    norm_matrix = matrix / col_sums
    # Öncelik vektörü (satır ortalaması)
    priority = norm_matrix.mean(axis=1)
    # λ_max hesapla
    weighted = matrix @ priority
    lambdas = weighted / priority
    lambda_max = lambdas.mean()
    # CI ve CR
    ci = (lambda_max - n) / (n - 1)
    ri_dict = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
    ri = ri_dict.get(n, 1.49)
    cr = ci / ri if ri != 0 else 0
    return cr, priority
# --- GÖMÜLÜ AYARLAR ---
USE_APPS_SCRIPT = True
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxom9lOJI1PT4dsKchrTCi-v25SdJODylfNCSOD41ctT7F16s7OgOnK0HWq_LXaOavLOQ/exec"
SEND_AS_JSON = True

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
araştırma kapsamında kullanılacak, üçüncü kişilerle paylaşılmayacaktır. Katkınız için teşekkür ederiz.
        """
    )

st.markdown("---")

# ======= Stil =======
st.markdown("""
<style>
.center { text-align: center; }
#likert-scope div[role="radiogroup"]{ gap: 2.2rem; }
#likert-scope div[role="radiogroup"] > label{
  min-width: 70px; display: inline-flex; justify-content: center; align-items: center;
}
#likert-scope div[role="radiogroup"] > label span{ font-size: 0 !important; line-height: 0; }
.likert-sep { margin: .30rem 0 .40rem 0; border: 0; border-top: .5px solid #ddd; }
@media (max-width: 640px){
  #likert-scope .center{ font-size: .9rem; }
  #likert-scope div[role="radiogroup"]{ gap: .9rem; }
  #likert-scope div[role="radiogroup"] > label{ min-width: 36px; }
  .stButton > button { width: 100%; }
}
</style>
""", unsafe_allow_html=True)

# ======= Sabitler =======
LIKERT_OPTIONS = ["Kesinlikle Katılıyorum","Katılıyorum","Kararsızım","Katılmıyorum","Kesinlikle Katılmıyorum"]
LIKERT_MAP = {"Kesinlikle Katılıyorum":5,"Katılıyorum":4,"Kararsızım":3,"Katılmıyorum":2,"Kesinlikle Katılmıyorum":1}

# ======= AHP Soru Grupları =======
comparison_sections = [
    {
        "title": "**Demografik** kriteri hangisini ne derecede etkiler?",
        "pairs": [
            ("Demografik", "Yaşam Tarzı"),
            ("Demografik", "Davranış"),
            ("Yaşam Tarzı", "Davranış"),
        ],
    },
    {
        "title": "**Davranış** kriteri hangisini ne derecede etkiler?",
        "pairs": [
            ("Demografik", "Yaşam Tarzı"),
        ],
    },
    {
        "title": "**Pozisyon** kriteri hangisini daha çok etkiler?",
        "pairs": [
            ("Dakiklik", "Sessizlik"),
        ],
    },
    {
        "title": "**Yaş** kriteri hangisini ne derecede etkiler?",
        "pairs": [
            ("Sigara Kullanımı", "Müzik Tercihi"),
            ("Eğitim", "Medeni Hal"),
        ],
    },
    {
        "title": "**Cinsiyet** kriteri hangisini ne derecede etkiler?",
        "pairs": [
            ("Sessizlik", "Dakiklik"),
        ],
    },
    {
        "title": "**Eğitim** kriteri hangisini ne derecede etkiler?",
        "pairs": [
            ("Dakiklik", "Sessizlik"),
        ],
    },
]

# ======= Form =======
st.subheader("1) Kişisel Bilgiler")
with st.form("survey_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        gender = st.radio("Cinsiyetiniz", ["Kadın", "Erkek"], horizontal=True)
        marital = st.radio("Medeni hâliniz", ["Evli", "Bekâr"], horizontal=True)
        smoking = st.radio("Sigara kullanımı", ["Evet", "Hayır"], horizontal=True)
    with c2:
        age = st.selectbox("Yaş aralığınız", ["18–29", "30–44", "45–59", "60+"])
        edu = st.selectbox("Eğitim durumunuz", ["İlkokul","Ortaokul","Lise","Ön Lisans","Lisans","Yüksek Lisans","Doktora"])
        position = st.selectbox("Çalışan pozisyonunuz", ["Stajyer","Saha Personeli","Ofis Görevlisi","İdari Personel","Yeni Mezun / Junior","Orta Düzey","Kıdemli","Takım Lideri","Yönetici","Üst Yönetim"])
    with c3:
        music = st.multiselect(
            "Araç içinde dinlemekten hoşlandığınız müzik tür(ler)i",
            ["Pop","Rock","Caz","Klasik","Rap / Hip Hop","Elektronik / Dance",
             "Türk Halk Müziği","Türk Sanat Müziği","Arabesk","Blues / Soul"]
        )

    st.markdown("---")

    c4, c5 = st.columns(2)
    with c4:
        punctuality_opt = st.radio(
            "Randevu ve yolculuklara geç kalma durumum sık yaşanır.",
            LIKERT_OPTIONS, index=2, horizontal=False
        )
    with c5:
        silence_opt = st.radio(
            "Yolculuk sırasında genellikle sessiz kalmayı tercih ederim.",
            LIKERT_OPTIONS, index=2, horizontal=False
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
        "Araç içinde birlikte seyahat edeceğim kişilerin **dakik** olmasını tercih ederim.",
        "Araç içinde birlikte seyahat edeceğim kişilerin yolculuk sırasında **sessiz olmasını** tercih ederim."
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

    # --- AHP: Yeni soru grupları ---
    st.markdown("---")
    st.subheader("3) Kriterleri Kıyaslayın ve Önem Derecesini Seçin")

    st.caption(
        "- Demografik özellikler: yaş, cinsiyet, eğitim, medeni hal, pozisyon\n"
        "- Davranış: dakiklik, sessizlik\n"
        "- Yaşam tarzı: sigara kullanımı, müzik tercihleri\n"
        "- Her satırda iki kriteri karşılaştırın. Kaydırma çubuğuyla hem hangisinin daha önemli olduğunu "
        "hem de ne kadar daha önemli olduğunu seçin: "
        "ortadaki **1** eşit önem; sola doğru **2–9** sol kriter daha önemli; "
        "sağa doğru **2–9** sağ kriter daha önemli (sayı büyüdükçe fark artar)."
    )

    display_values = ["9L","8L","7L","6L","5L","4L","3L","2L","1","2R","3R","4R","5R","6R","7R","8R","9R"]
    labels = ["9","8","7","6","5","4","3","2","1","2","3","4","5","6","7","8","9"]

    all_pairwise = []

    for sec_idx, section in enumerate(comparison_sections):
        st.markdown(f"#### {section['title']}")

        for pair_idx, (left, right) in enumerate(section["pairs"]):
            key = f"ahp_{sec_idx}_{pair_idx}"

            st.markdown(
                "<div style='padding:0.4rem 0.6rem; border-radius:6px; "
                "border:1px solid #eee; margin-bottom:0.6rem;'>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**{left}** mı yoksa **{right}** mı?", unsafe_allow_html=True)

            c_left, c_slider, c_right = st.columns([1.5, 6, 1.5])
            with c_left:
                st.markdown(f"<div style='text-align:left; font-weight:600;'>{left}</div>", unsafe_allow_html=True)

            with c_slider:
                selected = st.select_slider(
                    key,
                    options=display_values,
                    value="1",
                    format_func=lambda x: labels[display_values.index(x)],
                    key=key,
                    label_visibility="collapsed",
                )

                numbers_html = (
                    "<div style='display:flex; justify-content:space-between; "
                    "font-size:0.75rem; color:#666; margin-top:2px;'>"
                )
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

            all_pairwise.append({
                "section": section["title"],
                "left": left,
                "right": right,
                "raw_value": selected,
                "preferred": preferred,
                "ratio": ratio,
            })

    st.markdown("---")
    consent = st.checkbox("Gönüllü olarak katılıyorum ve verdiğim bilgilerin araştırma kapsamında kullanılmasını onaylıyorum.")
    submitted = st.form_submit_button("Gönder", use_container_width=True, type="primary")






# ======= AHP Tutarlılık Fonksiyonu =======
import numpy as np

def calc_ahp_cr(matrix):
    """3x3 AHP matrisi için Tutarlılık Oranı (CR) hesaplar."""
    n = matrix.shape[0]
    # Sütun toplamlarına bölerek normalize et
    col_sums = matrix.sum(axis=0)
    norm_matrix = matrix / col_sums
    # Öncelik vektörü (satır ortalaması)
    priority = norm_matrix.mean(axis=1)
    # λ_max hesapla
    weighted = matrix @ priority
    lambdas = weighted / priority
    lambda_max = lambdas.mean()
    # CI ve CR
    ci = (lambda_max - n) / (n - 1)
    ri_dict = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
    ri = ri_dict.get(n, 1.49)
    cr = ci / ri if ri != 0 else 0
    return cr, priority


# ======= Gönderim =======
if submitted:
    if not consent:
        st.error("Lütfen katılım onay kutusunu işaretleyiniz.")
    else:
        # --- AHP Tutarlılık Kontrolü (ilk soru grubu: 3×3 matris) ---
        # İlk 3 karşılaştırma → Demografik, Yaşam Tarzı, Davranış
        group_names = ["Demografik", "Yaşam Tarzı", "Davranış"]
        n_g = len(group_names)
        ahp_matrix = np.ones((n_g, n_g))

        for entry in all_pairwise[:3]:  # ilk 3 çift (ilk soru grubuna ait)
            i = group_names.index(entry["left"])
            j = group_names.index(entry["right"])
            val = entry["raw_value"]
            if val == "1":
                ahp_matrix[i][j] = 1
                ahp_matrix[j][i] = 1
            elif val.endswith("L"):
                r = int(val[:-1])
                ahp_matrix[i][j] = r
                ahp_matrix[j][i] = 1 / r
            else:
                r = int(val[:-1])
                ahp_matrix[i][j] = 1 / r
                ahp_matrix[j][i] = r

        cr, priority = calc_ahp_cr(ahp_matrix)

        if cr > 0.10:
            st.error(
                f"⚠️ Kriter grupları karşılaştırmanız **tutarsız** çıktı (CR = {cr:.3f} > 0.10). "
                f"Lütfen **3. bölümdeki** ilk üç karşılaştırmayı (Demografik, Yaşam Tarzı, Davranış) "
                f"gözden geçirip tekrar doldurunuz."
            )
            st.info(
                "💡 **Tutarlılık nedir?** Örneğin A, B'den önemliyse ve B, C'den önemliyse, "
                "A'nın C'den de önemli olması beklenir. Aksi takdirde tutarsızlık oluşur."
            )
        else:
            # Tutarlı → kaydet
            row = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "gender": gender,
                "marital": marital,
                "age_range": age,
                "education": edu,
                "position": position,
                "smoking": smoking,
                "music": "; ".join(music) if music else "",
                "punctuality_late": int(LIKERT_MAP[punctuality_opt]),
                "punctuality_score": 6 - int(LIKERT_MAP[punctuality_opt]),
                "punctuality_label": punctuality_opt,
                "silence": int(LIKERT_MAP[silence_opt]),
                "silence_label": silence_opt,
                "ahp_cr": round(cr, 4),
            }

            # Likert
            for i in range(1, len(likert_prompts) + 1):
                opt = likert_answers[f"Q{i}_opt"]
                row[f"Q{i}"] = int(LIKERT_MAP[opt])
                row[f"Q{i}_label"] = opt

            # AHP — tek JSON sütunu
            row["ahp_json"] = json.dumps(all_pairwise, ensure_ascii=False)

            # Google Sheets'e gönder
            if USE_APPS_SCRIPT and WEB_APP_URL.strip() != "":
                try:
                    payload = row.copy()
                    if SEND_AS_JSON:
                        headers = {"Content-Type": "application/json"}
                        r = requests.post(WEB_APP_URL, headers=headers, data=json.dumps(payload), timeout=10)
                    else:
                        r = requests.post(WEB_APP_URL, data=payload, timeout=10)
                    if r.status_code == 200:
                        st.success(f"✅ Yanıtlarınız kaydedildi (CR = {cr:.3f}). Katılımınız için teşekkürler.")
                    else:
                        st.warning(f"Web App cevap kodu: {r.status_code}. Detay: {r.text[:200]}")
                except Exception as e:
                    st.error(f"Yanıtlarınız kaydedilemedi!: {e}")
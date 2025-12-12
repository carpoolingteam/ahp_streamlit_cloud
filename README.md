# AHP Streamlit Anketi (7 Kriter, 1–9 Saaty Ölçeği)

Bu repo, 7 kriterli AHP anketini Streamlit ile çalıştırır.

## 🚀 Yerel Çalıştırma
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## ☁️ Streamlit Cloud'da Yayınlama
1. Bu dosyaları GitHub reposuna yükleyin.
2. https://share.streamlit.io adresinden **Deploy an app** deyin.
3. Repo ve branch'i seçip `streamlit_app.py` dosyasını başlangıç olarak belirtin.
4. Yayına alındıktan sonra size `https://<uygulama-adı>.streamlit.app` şeklinde kalıcı bir URL verilir.

### URL ile Kriterleri Ön-Doldurma
Uygulama linkinin sonuna şu parametreleri ekleyebilirsiniz:
```
?c1=Maliyet&c2=Kalite&c3=Zaman&c4=Risk&c5=Esneklik&c6=Sürdürülebilirlik&c7=Müşteri
```

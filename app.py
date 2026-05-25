import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import os

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Eğirdir Gölü KDS", page_icon="🌊", layout="wide")

# 2. VERİ YÜKLEME (Önbelleğe alarak siteyi hızlandırır)
@st.cache_data
def load_data():
    dosya_yolu = "Tez_Veriler_5_Scenarios_with_99CI.csv"
    if os.path.exists(dosya_yolu):
        df = pd.read_csv(dosya_yolu, sep=None, engine='python')
        df['Date'] = pd.to_datetime(df['Date'])
        df['Year'] = df['Date'].dt.year
        return df
    else:
        st.error(f"⚠️ {dosya_yolu} bulunamadı! Lütfen KDS ile aynı klasörde olduğundan emin olun.")
        return None

df = load_data()

if df is not None:
    # 3. YAN MENÜ (SIDEBAR) TASARIMI
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Egirdir_Lake.jpg/800px-Egirdir_Lake.jpg", use_column_width=True)
    st.sidebar.title("KONTROL PANELİ")
    st.sidebar.markdown("---")
    
    # Senaryo Sözlüğü
    scenario_dict = {
        "Baseline (Geçmiş İklim Eğilimi)": "Volume_Cumulative_base",
        "CanESM5 SSP1-2.6 (İyimser)": "Volume_Cumulative_SSP1_26",
        "CanESM5 SSP2-4.5 (Orta Yol)": "Volume_Cumulative_SSP2_45",
        "CanESM5 SSP5-8.5 (Kötü Durum)": "Volume_Cumulative_SSP5_85"
    }
    
    secilen_senaryo_adi = st.sidebar.selectbox("🌡️ İklim Senaryosunu Seçiniz:", list(scenario_dict.keys()))
    secilen_sutun = scenario_dict[secilen_senaryo_adi]
    
    hedef_yil = st.sidebar.slider("📅 Hedef Yılı Seçiniz:", min_value=2026, max_value=2050, value=2050, step=1)
    
    st.sidebar.markdown("---")
    st.sidebar.info("📌 **Bilgi:** Bu sistem, Random Forest makine öğrenmesi algoritması ve IPCC AR6 / MedECC MAR1 iklim standartları kullanılarak geliştirilmiştir.")

    # 4. ANA EKRAN TASARIMI
    st.title("🌊 Eğirdir Gölü Su Kaynakları Karar Destek Sistemi (KDS)")
    st.markdown(f"**Seçilen Yıl:** {hedef_yil} | **Aktif Senaryo:** {secilen_senaryo_adi}")
    
    # Seçilen yıla ait veriyi filtrele (O yılın son ayındaki kümülatif durumu al)
    df_yil = df[df['Year'] == hedef_yil]
    
    if not df_yil.empty:
        son_deger = df_yil.iloc[-1]
        tahmin_hacim = son_deger[secilen_sutun]
        alt_sinir = son_deger['Volume_Cumulative_Lower_99CI']
        ust_sinir = son_deger['Volume_Cumulative_Upper_99CI']
        
        # Risk Durumu Analizi
        if tahmin_hacim < alt_sinir:
            durum_mesaji = "🚨 KRİTİK SEVİYE: Ekstrem Hacim Kaybı Sinyali!"
            renk = "inverse"
        else:
            durum_mesaji = "✅ NORMAL SEVİYE: %99 Güven Aralığında Stabil"
            renk = "normal"

        # Üst Skor Kartları (Metrikler)
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Tahmini Rezervuar Hacmi", value=f"{tahmin_hacim:,.2f} hm³")
        col2.metric(label="%99 Alt Sınır (Risk)", value=f"{alt_sinir:,.2f} hm³")
        col3.metric(label="Sistem Durumu", value=durum_mesaji, delta_color=renk)
        
        st.markdown("---")
        
        # 5. ALT BÖLÜM: GRAFİK VE HARİTA (Yan yana)
        col_grafik, col_harita = st.columns((2, 1))
        
        with col_grafik:
            st.subheader(f"Gelecek Projeksiyonu (2020 - {hedef_yil})")
            # Sadece seçilen yıla kadar olan veriyi al
            df_plot = df[df['Year'] <= hedef_yil]
            
            # Plotly ile etkileşimli grafik
            fig = px.line(df_plot, x='Date', y=secilen_sutun, 
                          title=f"{secilen_senaryo_adi} Hacim Eğrisi",
                          labels={'Date': 'Tarih', secilen_sutun: 'Kümülatif Hacim (hm³)'})
            fig.add_scatter(x=df_plot['Date'], y=df_plot['Volume_Cumulative_Lower_99CI'], 
                            mode='lines', name='%99 Alt Sınır', line=dict(dash='dot', color='red'))
            st.plotly_chart(fig, use_container_width=True)

        with col_harita:
            st.subheader("İstasyon Konumları")
            # Folium ile QGIS benzeri akademik harita
            m = folium.Map(location=[38.0, 30.8], zoom_start=9, tiles="CartoDB positron")
            
            # İstasyon pinleri
            istasyonlar = {
                "Eğirdir": [37.87, 30.85],
                "Senirkent": [38.09, 30.55],
                "Yalvaç": [38.30, 31.18]
            }
            
            for ad, kordinat in istasyonlar.items():
                folium.Marker(
                    location=kordinat,
                    popup=f"<b>{ad} İstasyonu</b><br>Meteorolojik Girdi",
                    icon=folium.Icon(color="darkblue", icon="info-sign"),
                ).add_to(m)
            
            # Haritayı ekrana bas
            st_folium(m, width=400, height=350)

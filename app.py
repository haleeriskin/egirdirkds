import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import os

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Eğirdir Gölü KDS", page_icon="🌊", layout="wide")

# 2. SABİT EŞİK DEĞERLERİ
KRITIK_ESIK = 2150  # hm³
UYARI_ESIK = 2400   # hm³

# 3. VERİ YÜKLEME
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

    # 4. YAN MENÜ TASARIMI
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/0/0b/Yedi_Renkli_G%C3%B6l_%E2%80%93_E%C4%9Firdir.jpg",
        use_container_width=True
    )

    st.sidebar.title("KONTROL PANELİ")
    st.sidebar.markdown("---")

    # Senaryo Sözlüğü
    scenario_dict = {
        "Baseline (Geçmiş İklim Eğilimi)": "Volume_Cumulative_base",
        "CanESM5 SSP1-2.6 (İyimser)": "Volume_Cumulative_SSP1_26",
        "CanESM5 SSP2-4.5 (Orta Yol)": "Volume_Cumulative_SSP2_45",
        "CanESM5 SSP5-8.5 (Kötü Durum)": "Volume_Cumulative_SSP5_85"
    }

    secilen_senaryo_adi = st.sidebar.selectbox(
        "🌡️ İklim Senaryosunu Seçiniz:",
        list(scenario_dict.keys())
    )

    secilen_sutun = scenario_dict[secilen_senaryo_adi]

    hedef_yil = st.sidebar.slider(
        "📅 Hedef Yılı Seçiniz:",
        min_value=2026,
        max_value=2050,
        value=2050,
        step=1
    )

    st.sidebar.markdown("---")

    st.sidebar.info(
        "📌 **Bilgi:** Bu sistem, Random Forest makine öğrenmesi algoritması "
        "ve IPCC AR6 / MedECC MAR1 iklim standartları kullanılarak geliştirilmiştir."
    )

    # 5. ANA EKRAN TASARIMI
    st.title("🌊 Eğirdir Gölü Su Kaynakları Karar Destek Sistemi (KDS)")
    st.markdown(f"**Seçilen Yıl:** {hedef_yil} | **Aktif Senaryo:** {secilen_senaryo_adi}")

    # Seçilen yıla ait veri
    df_yil = df[df['Year'] == hedef_yil]

    if not df_yil.empty:

        # O yılın son ayındaki kümülatif durumu al
        son_deger = df_yil.iloc[-1]

        tahmin_hacim = son_deger[secilen_sutun]
        alt_sinir = son_deger['Volume_Cumulative_Lower_99CI']
        ust_sinir = son_deger['Volume_Cumulative_Upper_99CI']

        # 6. RİSK DURUMU ANALİZİ
        # Artık güven aralığına göre değil, sabit eşiklere göre çalışır.

        if tahmin_hacim < KRITIK_ESIK:
            durum_mesaji = "🚨 KRİTİK SEVİYE"
            durum_aciklama = "Tahmini hacim 2150 hm³ kritik eşiğinin altına düşmüştür."
            renk = "inverse"
            arka_plan_rengi = "#ffebee"   # açık kırmızı
            uyari_kutu_rengi = "#ffcdd2"

        elif tahmin_hacim < UYARI_ESIK:
            durum_mesaji = "⚠️ UYARI SEVİYESİ"
            durum_aciklama = "Tahmini hacim 2400 hm³ uyarı eşiğinin altına düşmüştür."
            renk = "off"
            arka_plan_rengi = "#fff8e1"   # açık sarı
            uyari_kutu_rengi = "#ffecb3"

        else:
            durum_mesaji = "✅ NORMAL SEVİYE"
            durum_aciklama = "Tahmini hacim uyarı ve kritik eşik değerlerinin üzerindedir."
            renk = "normal"
            arka_plan_rengi = "#ffffff"   # normal beyaz
            uyari_kutu_rengi = "#e8f5e9"

        # 7. SAYFA ARKA PLAN RENGİ
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-color: {arka_plan_rengi};
            }}

            .uyari-kutusu {{
                background-color: {uyari_kutu_rengi};
                padding: 14px;
                border-radius: 10px;
                margin-top: 10px;
                margin-bottom: 15px;
                font-size: 17px;
                font-weight: 600;
                border: 1px solid rgba(0,0,0,0.12);
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        # 8. ÜST SKOR KARTLARI
        col1, col2, col3 = st.columns(3)

        col1.metric(
            label="Tahmini Rezervuar Hacmi",
            value=f"{tahmin_hacim:,.2f} hm³"
        )

        col2.metric(
            label="Kritik Eşik Değeri",
            value=f"{KRITIK_ESIK:,.0f} hm³"
        )

        col3.metric(
            label="Sistem Durumu",
            value=durum_mesaji,
            delta_color=renk
        )

        st.markdown(
            f"""
            <div class="uyari-kutusu">
            {durum_aciklama}<br>
            <b>Karar Mantığı:</b> 
            2150 hm³ altı kritik seviye, 2150–2400 hm³ arası uyarı seviyesi, 
            2400 hm³ üzeri normal seviye olarak değerlendirilir.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")

        # 9. ALT BÖLÜM: GRAFİK VE HARİTA
        col_grafik, col_harita = st.columns((2, 1))

        with col_grafik:
            st.subheader(f"Gelecek Projeksiyonu (2020 - {hedef_yil})")

            # Seçilen yıla kadar olan tüm ayları alır.
            # Eğer CSV aylık ise grafik aylık değerleri gösterir.
            df_plot = df[df['Year'] <= hedef_yil].copy()

            # Plotly ile etkileşimli ve yumuşatılmış çizgi grafik
            fig = px.line(
                df_plot,
                x='Date',
                y=secilen_sutun,
                title=f"{secilen_senaryo_adi} Hacim Eğrisi",
                labels={
                    'Date': 'Tarih',
                    secilen_sutun: 'Kümülatif Hacim (hm³)'
                },
                line_shape="spline"
            )

            fig.update_traces(
                name="Tahmini Hacim",
                showlegend=True,
                line=dict(width=3)
            )

            # %99 Alt Sınır
            fig.add_scatter(
                x=df_plot['Date'],
                y=df_plot['Volume_Cumulative_Lower_99CI'],
                mode='lines',
                name='%99 Alt Sınır',
                line=dict(dash='dot', color='red'),
                line_shape="spline"
            )

            # Kritik eşik çizgisi: 2150 hm³
            fig.add_hline(
                y=KRITIK_ESIK,
                line_dash="solid",
                line_color="darkred",
                line_width=2,
                annotation_text="Kritik Eşik: 2150 hm³",
                annotation_position="top left"
            )

            fig.update_layout(
                hovermode="x unified",
                legend_title_text="Gösterge",
                yaxis_title="Kümülatif Hacim (hm³)",
                xaxis_title="Tarih"
            )

            st.plotly_chart(fig, use_container_width=True)

        with col_harita:
            st.subheader("İstasyon Konumları")

            m = folium.Map(
                location=[38.0, 30.8],
                zoom_start=9,
                tiles="CartoDB positron"
            )

            istasyonlar = {
                "Eğirdir": [37.87, 30.85],
                "Senirkent": [38.09, 30.55],
                "Yalvaç": [38.30, 31.18]
            }

            for ad, koordinat in istasyonlar.items():
                folium.Marker(
                    location=koordinat,
                    popup=f"<b>{ad} İstasyonu</b><br>Meteorolojik Girdi",
                    icon=folium.Icon(color="darkblue", icon="info-sign"),
                ).add_to(m)

            st_folium(m, width=400, height=350)

    else:
        st.warning(f"⚠️ {hedef_yil} yılına ait veri bulunamadı.")

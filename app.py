import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import os

# ============================================================
# 1. SAYFA AYARLARI
# ============================================================

st.set_page_config(
    page_title="Eğirdir Gölü KDS",
    page_icon="🌊",
    layout="wide"
)

# ============================================================
# 2. SABİT EŞİK DEĞERLERİ
# ============================================================

KRITIK_ESIK = 2150  # hm³
UYARI_ESIK = 2400   # hm³

# ============================================================
# 3. VERİ YÜKLEME
# ============================================================

@st.cache_data
def load_data():
    dosya_yolu = "Tez_Veriler_5_Scenarios_with_99CI.csv"

    if os.path.exists(dosya_yolu):
        df = pd.read_csv(dosya_yolu, sep=None, engine="python")
        df["Date"] = pd.to_datetime(df["Date"])
        df["Year"] = df["Date"].dt.year
        return df
    else:
        st.error(
            f"⚠️ {dosya_yolu} bulunamadı! "
            "Lütfen CSV dosyasının KDS ile aynı klasörde olduğundan emin olun."
        )
        return None


df = load_data()

# ============================================================
# 4. ANA UYGULAMA
# ============================================================

if df is not None:

    # ------------------------------------------------------------
    # 4.1. YAN MENÜ
    # ------------------------------------------------------------

    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/0/0b/Yedi_Renkli_G%C3%B6l_%E2%80%93_E%C4%9Firdir.jpg",
        use_container_width=True
    )

    st.sidebar.title("KONTROL PANELİ")
    st.sidebar.markdown("---")

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
        min_value=2021,
        max_value=2050,
        value=2050,
        step=1
    )

    st.sidebar.markdown("---")

    st.sidebar.info(
        "📌 **Bilgi:** Bu sistem, Random Forest makine öğrenmesi algoritması "
        "ve IPCC AR6 / MedECC MAR1 iklim standartları kullanılarak geliştirilmiştir."
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Eşik Değerleri")
    st.sidebar.markdown(f"🚨 **Kritik Eşik:** {KRITIK_ESIK:,.0f} hm³")
    st.sidebar.markdown(f"⚠️ **Uyarı Eşiği:** {UYARI_ESIK:,.0f} hm³")

    # ------------------------------------------------------------
    # 4.2. ANA BAŞLIK
    # ------------------------------------------------------------

    st.title("🌊 Eğirdir Gölü Su Kaynakları Karar Destek Sistemi (KDS)")

    st.markdown(
        f"**Seçilen Yıl:** {hedef_yil} | "
        f"**Aktif Senaryo:** {secilen_senaryo_adi}"
    )

    # ------------------------------------------------------------
    # 4.3. SEÇİLEN YIL VERİSİ
    # ------------------------------------------------------------

    df_yil = df[df["Year"] == hedef_yil]

    if not df_yil.empty:

        son_deger = df_yil.iloc[-1]

        tahmin_hacim = son_deger[secilen_sutun]
        alt_sinir = son_deger["Volume_Cumulative_Lower_99CI"]
        ust_sinir = son_deger["Volume_Cumulative_Upper_99CI"]

        # ------------------------------------------------------------
        # 4.4. RİSK DURUMU ANALİZİ
        # ------------------------------------------------------------

        if tahmin_hacim < KRITIK_ESIK:
            durum_mesaji = (
                "🚨 KRİTİK SEVİYE: Tahmini hacim 2150 hm³ kritik eşiğinin altına düşmüştür."
            )
            durum_kisa = "KRİTİK"
            sayfa_rengi = "#ffebee"      # açık kırmızı
            kutu_rengi = "#b71c1c"       # koyu kırmızı
            metin_rengi = "white"

        elif tahmin_hacim < UYARI_ESIK:
            durum_mesaji = (
                "⚠️ UYARI SEVİYESİ: Tahmini hacim 2400 hm³ uyarı eşiğinin altına düşmüştür."
            )
            durum_kisa = "UYARI"
            sayfa_rengi = "#fff8e1"      # açık sarı
            kutu_rengi = "#f57f17"       # koyu sarı/turuncu
            metin_rengi = "white"

        else:
            durum_mesaji = (
                "✅ NORMAL SEVİYE: Tahmini hacim operasyonel eşik değerlerinin üzerindedir."
            )
            durum_kisa = "NORMAL"
            sayfa_rengi = "#ffffff"      # beyaz
            kutu_rengi = "#1b5e20"       # koyu yeşil
            metin_rengi = "white"

        # ------------------------------------------------------------
        # 4.5. SAYFA RENK STİLİ
        # ------------------------------------------------------------

        st.markdown(
            f"""
            <style>
            .stApp {{
                background-color: {sayfa_rengi};
            }}

            .risk-box {{
                padding: 18px;
                border-radius: 12px;
                background-color: {kutu_rengi};
                color: {metin_rengi};
                font-size: 20px;
                font-weight: bold;
                text-align: center;
                margin-top: 15px;
                margin-bottom: 20px;
                box-shadow: 0px 2px 8px rgba(0,0,0,0.15);
            }}

            .threshold-info {{
                padding: 12px;
                border-radius: 10px;
                background-color: rgba(255,255,255,0.80);
                border: 1px solid #dddddd;
                margin-bottom: 15px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        # ------------------------------------------------------------
        # 4.6. ÜST SKOR KARTLARI
        # ------------------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            label="Tahmini Rezervuar Hacmi",
            value=f"{tahmin_hacim:,.2f} hm³"
        )

        col2.metric(
            label="Kritik Eşik",
            value=f"{KRITIK_ESIK:,.0f} hm³"
        )

        col3.metric(
            label="Uyarı Eşiği",
            value=f"{UYARI_ESIK:,.0f} hm³"
        )

        col4.metric(
            label="Sistem Durumu",
            value=durum_kisa
        )

        st.markdown(
            f"<div class='risk-box'>{durum_mesaji}</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='threshold-info'>
            <b>Karar Mantığı:</b>
            Hacim <b>{KRITIK_ESIK:,.0f} hm³</b> altına düşerse <b>kritik seviye</b>,
            <b>{KRITIK_ESIK:,.0f}–{UYARI_ESIK:,.0f} hm³</b> aralığında ise <b>uyarı seviyesi</b>,
            <b>{UYARI_ESIK:,.0f} hm³</b> üzerinde ise <b>normal seviye</b> olarak değerlendirilir.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")

        # ------------------------------------------------------------
        # 4.7. GRAFİK VE HARİTA
        # ------------------------------------------------------------

        col_grafik, col_harita = st.columns((2, 1))

        with col_grafik:

            st.subheader(f"Gelecek Projeksiyonu: 2020 - {hedef_yil}")

            df_plot = df[df["Year"] <= hedef_yil]

            fig = px.line(
                df_plot,
                x="Date",
                y=secilen_sutun,
                title=f"{secilen_senaryo_adi} Hacim Eğrisi",
                labels={
                    "Date": "Tarih",
                    secilen_sutun: "Kümülatif Hacim (hm³)"
                }
            )

            # Seçilen senaryo çizgisi
            fig.update_traces(
                name="Tahmini Hacim",
                showlegend=True,
                line=dict(width=3)
            )

            # %99 alt güven sınırı
            fig.add_scatter(
                x=df_plot["Date"],
                y=df_plot["Volume_Cumulative_Lower_99CI"],
                mode="lines",
                name="%99 Alt Sınır",
                line=dict(dash="dot", color="red", width=2)
            )

            # %99 üst güven sınırı
            fig.add_scatter(
                x=df_plot["Date"],
                y=df_plot["Volume_Cumulative_Upper_99CI"],
                mode="lines",
                name="%99 Üst Sınır",
                line=dict(dash="dot", color="green", width=2)
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
                xaxis_title="Tarih",
                yaxis_title="Kümülatif Hacim (hm³)",
                hovermode="x unified",
                legend_title_text="Gösterge",
                height=500
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
                    icon=folium.Icon(color="darkblue", icon="info-sign")
                ).add_to(m)

            st_folium(m, width=450, height=500)

        # ------------------------------------------------------------
        # 4.8. ALT BİLGİ
        # ------------------------------------------------------------

        st.markdown("---")

        st.caption(
            "Not: 2150 hm³ kritik eşiği grafik üzerinde sabit yatay çizgi olarak gösterilmiştir. "
            "2400 hm³ uyarı eşiği ise grafik üzerinde gösterilmemekte, yalnızca karar destek mekanizmasında kullanılmaktadır."
        )

    else:
        st.warning(
            f"⚠️ {hedef_yil} yılına ait veri bulunamadı. "
            "Lütfen CSV dosyasındaki tarih aralığını kontrol ediniz."
        )

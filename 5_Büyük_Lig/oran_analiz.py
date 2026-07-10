import streamlit as st
import pandas as pd
import glob
import os
import numpy as np

# Sayfa Yapılandırması
st.set_page_config(page_title="Oran Analiz Paneli", layout="wide")
st.title("⚽ Gelişmiş Futbol Oran Analizörü")

@st.cache_data
def verileri_oku_v3():
    tum_dosyalar = glob.glob("**/*.csv", recursive=True)
    dataframes = []

    sutun_degisimleri = {
        'Home': 'HomeTeam', 'Away': 'AwayTeam',
        'HGFT': 'FTHG', 'AGFT': 'FTAG',
        'HG1st': 'HTHG', 'AG1st': 'HTAG',
        'bet365-H': 'B365H', 'bet365-D': 'B365D', 'bet365-A': 'B365A',
        'HG': 'FTHG', 'AG': 'FTAG', 'Res': 'FTR',
        'Div': 'Lig', 'League': 'Lig', 'Competition': 'Lig'
    }

    for dosya in tum_dosyalar:
        try:
            dosya_adi = os.path.basename(dosya)
            if 'WorldCup' in dosya_adi:
                gecici_df = pd.read_csv(dosya, encoding='latin1', sep=';')
            else:
                gecici_df = pd.read_csv(dosya, encoding='latin1')

            gecici_df.rename(columns=sutun_degisimleri, inplace=True)
            gecici_df.columns = gecici_df.columns.str.replace(' ', '')
            gecici_df['Source_File'] = dosya_adi

            if 'Lig' not in gecici_df.columns:
                gecici_df['Lig'] = dosya_adi.replace('.csv', '')

            gecici_df = gecici_df.copy()

            dataframes.append(gecici_df)
        except Exception as e:
            pass

    if len(dataframes) > 0:
        df = pd.concat(dataframes, ignore_index=True)

        if 'Lig' in df.columns:
            df['Lig'] = df['Lig'].astype(str).str.strip()
            df['Lig'] = df['Lig'].str.replace(r'\s*\(\d+\)', '', regex=True)

            df.loc[df['Lig'].str.contains('World Cup', case=False, na=False) & ~df['Lig'].str.contains('Qualifiers', case=False, na=False), 'Lig'] = 'Dünya Kupası'
            df['Lig'] = df['Lig'].replace('WorldCupQualifiers', 'Dünya Kupası Elemeleri')

            if 'Country' in df.columns:
                df['Country'] = df['Country'].astype(str).str.strip()
                mask = (df['Country'] != 'nan') & (df['Country'] != '') & (df['Country'].notna())
                df.loc[mask, 'Lig'] = df.loc[mask, 'Country'] + ' - ' + df.loc[mask, 'Lig']

            cince_mask = (df['Lig'] == 'Super League') & df['Source_File'].str.contains('CHN', case=False, na=False)
            df.loc[cince_mask, 'Lig'] = 'China - Super League'

            isvicre_mask = (df['Lig'] == 'Super League') & df['Source_File'].str.contains('SWZ', case=False, na=False)
            df.loc[isvicre_mask, 'Lig'] = 'Switzerland - Super League'

            yunan_mask = (df['Lig'] == 'Super League') & df['Source_File'].str.contains('G1', case=False, na=False)
            df.loc[yunan_mask, 'Lig'] = 'Greece - Super League'

            lig_isimleri = {
                'E0': 'Premier League (İngiltere)', 'E1': 'Championship (İngiltere)',
                'D1': 'Bundesliga (Almanya)', 'D2': '2. Bundesliga (Almanya)',
                'I1': 'Serie A (İtalya)', 'SP1': 'La Liga (İspanya)',
                'F1': 'Ligue 1 (Fransa)', 'N1': 'Eredivisie (Hollanda)',
                'T1': 'Süper Lig (Türkiye)'
            }
            df['Lig'] = df['Lig'].replace(lig_isimleri)

        df = df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'])

        if 'FTR' not in df.columns:
            df['FTR'] = np.nan

        if 'FTHG' in df.columns and 'FTAG' in df.columns:
            eksik_ftr = df['FTR'].isnull()
            df.loc[eksik_ftr & (df['FTHG'] > df['FTAG']), 'FTR'] = 'H'
            df.loc[eksik_ftr & (df['FTHG'] == df['FTAG']), 'FTR'] = 'D'
            df.loc[eksik_ftr & (df['FTHG'] < df['FTAG']), 'FTR'] = 'A'

        oran_sutunlari = ['B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA', 'BFECH', 'BFECD', 'BFECA']
        for col in oran_sutunlari:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    return pd.DataFrame()


df = verileri_oku_v3()
st.write("✅ CHECKPOINT 1: Veri okuma tamamlandı")

if df.empty:
    st.error("Veriler okunamadı. Klasör yolunu kontrol et.")
else:
    st.sidebar.success(f"Toplam {len(df)} tekil maç yüklendi.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌍 Lig Filtresi")
    mevcut_ligler = sorted(df['Lig'].dropna().unique().tolist()) if 'Lig' in df.columns else []
    secilen_ligler = st.sidebar.multiselect("Lig Seçin (Örn: Bundesliga)", mevcut_ligler)

    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Oran Filtreleri")
    tolerans = st.sidebar.slider("Tolerans (Esneklik Payı)", min_value=0.00, max_value=0.50, value=0.03, step=0.01)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🟩 Bet365 Açılış")
    acilis_ms1 = st.sidebar.number_input("MS 1 Açılış (B365H)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    acilis_msx = st.sidebar.number_input("MS X Açılış (B365D)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    acilis_ms2 = st.sidebar.number_input("MS 2 Açılış (B365A)", min_value=1.01, value=None, step=0.01, placeholder="Boş")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🟥 Bet365 Kapanış")
    kapanis_ms1 = st.sidebar.number_input("MS 1 Kapanış (B365CH)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    kapanis_msx = st.sidebar.number_input("MS X Kapanış (B365CD)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    kapanis_ms2 = st.sidebar.number_input("MS 2 Kapanış (B365CA)", min_value=1.01, value=None, step=0.01, placeholder="Boş")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🟨 Betfair Borsa Kapanış")
    kapanis_bf1 = st.sidebar.number_input("MS 1 Betfair Kapanış (BFECH)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    kapanis_bfx = st.sidebar.number_input("MS X Betfair Kapanış (BFECD)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    kapanis_bf2 = st.sidebar.number_input("MS 2 Betfair Kapanış (BFECA)", min_value=1.01, value=None, step=0.01, placeholder="Boş")

    st.write("✅ CHECKPOINT 2: Sidebar widget'ları oluşturuldu")

    sonuclar = df.copy()

    if secilen_ligler and 'Lig' in sonuclar.columns:
        sonuclar = sonuclar[sonuclar['Lig'].isin(secilen_ligler)]

    if acilis_ms1 is not None and 'B365H' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365H'])
        sonuclar = sonuclar[sonuclar['B365H'].between(acilis_ms1 - tolerans, acilis_ms1 + tolerans)]
    if acilis_msx is not None and 'B365D' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365D'])
        sonuclar = sonuclar[sonuclar['B365D'].between(acilis_msx - tolerans, acilis_msx + tolerans)]
    if acilis_ms2 is not None and 'B365A' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365A'])
        sonuclar = sonuclar[sonuclar['B365A'].between(acilis_ms2 - tolerans, acilis_ms2 + tolerans)]

    if kapanis_ms1 is not None and 'B365CH' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365CH'])
        sonuclar = sonuclar[sonuclar['B365CH'].between(kapanis_ms1 - tolerans, kapanis_ms1 + tolerans)]
    if kapanis_msx is not None and 'B365CD' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365CD'])
        sonuclar = sonuclar[sonuclar['B365CD'].between(kapanis_msx - tolerans, kapanis_msx + tolerans)]
    if kapanis_ms2 is not None and 'B365CA' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365CA'])
        sonuclar = sonuclar[sonuclar['B365CA'].between(kapanis_ms2 - tolerans, kapanis_ms2 + tolerans)]

    if kapanis_bf1 is not None and 'BFECH' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['BFECH'])
        sonuclar = sonuclar[sonuclar['BFECH'].between(kapanis_bf1 - tolerans, kapanis_bf1 + tolerans)]
    if kapanis_bfx is not None and 'BFECD' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['BFECD'])
        sonuclar = sonuclar[sonuclar['BFECD'].between(kapanis_bfx - tolerans, kapanis_bfx + tolerans)]
    if kapanis_bf2 is not None and 'BFECA' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['BFECA'])
        sonuclar = sonuclar[sonuclar['BFECA'].between(kapanis_bf2 - tolerans, kapanis_bf2 + tolerans)]

    st.write(f"✅ CHECKPOINT 3: Filtreleme tamamlandı. Kalan satır: {len(sonuclar)}")

    st.subheader(f"📊 Kriterlere Uyan Toplam Maç Sayısı: {len(sonuclar)}")

    filtre_girildi_mi = any(v is not None for v in [acilis_ms1, acilis_msx, acilis_ms2, kapanis_ms1, kapanis_msx, kapanis_ms2, kapanis_bf1, kapanis_bfx, kapanis_bf2])

    if not filtre_girildi_mi and not secilen_ligler:
        st.info("👈 Lütfen sol menüden lig veya oran girin.")
    elif len(sonuclar) > 0:

        st.write("✅ CHECKPOINT 4: Analiz bloğuna girildi")

        st.markdown("---")
        st.markdown("### 📊 Filtreye Özel Ev Sahibi Avantajı (HFA) ve Değer (Value) Analizi")

        toplam_mac = len(sonuclar)
        ev_gal = len(sonuclar[sonuclar['FTR'] == 'H'])
        beraberlik = len(sonuclar[sonuclar['FTR'] == 'D'])
        dep_gal = len(sonuclar[sonuclar['FTR'] == 'A'])

        ev_oran = (ev_gal / toplam_mac) * 100
        ber_oran = (beraberlik / toplam_mac) * 100
        dep_oran = (dep_gal / toplam_mac) * 100

        ort_ev_gol = sonuclar['FTHG'].mean() if 'FTHG' in sonuclar.columns else 0
        ort_dep_gol = sonuclar['FTAG'].mean() if 'FTAG' in sonuclar.columns else 0
        hfa_gol_avantaji = ort_ev_gol - ort_dep_gol

        st.write("✅ CHECKPOINT 5: Metrikler hesaplandı")

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Ev Sahibi Galibiyet %", f"% {ev_oran:.1f}")
        m_col2.metric("Beraberlik %", f"% {ber_oran:.1f}")
        m_col3.metric("Deplasman Galibiyet %", f"% {dep_oran:.1f}")
        m_col4.metric("HFA Gol Dominansı", f"+{hfa_gol_avantaji:.2f}" if hfa_gol_avantaji >= 0 else f"{hfa_gol_avantaji:.2f}")

        st.write("✅ CHECKPOINT 6: Metrik kutuları gösterildi")

        value_verileri = []

        if acilis_ms1 is not None: value_verileri.append({"Bahis Tipi": "MS 1 (B365 Açılış)", "Girdiğiniz Oran": acilis_ms1, "Büro Olasılığı": f"% {(1 / acilis_ms1) * 100:.1f}", "Gerçekleşen Olasılık": f"% {ev_oran:.1f}", "Sapma (Value)": f"{ev_oran - ((1 / acilis_ms1) * 100):+.1f}%", "Durum": "✅ Değerli" if (ev_oran - ((1 / acilis_ms1) * 100)) > 0 else "❌ Değersiz"})
        if acilis_msx is not None: value_verileri.append({"Bahis Tipi": "MS X (B365 Açılış)", "Girdiğiniz Oran": acilis_msx, "Büro Olasılığı": f"% {(1 / acilis_msx) * 100:.1f}", "Gerçekleşen Olasılık": f"% {ber_oran:.1f}", "Sapma (Value)": f"{ber_oran - ((1 / acilis_msx) * 100):+.1f}%", "Durum": "✅ Değerli" if (ber_oran - ((1 / acilis_msx) * 100)) > 0 else "❌ Değersiz"})
        if acilis_ms2 is not None: value_verileri.append({"Bahis Tipi": "MS 2 (B365 Açılış)", "Girdiğiniz Oran": acilis_ms2, "Büro Olasılığı": f"% {(1 / acilis_ms2) * 100:.1f}", "Gerçekleşen Olasılık": f"% {dep_oran:.1f}", "Sapma (Value)": f"{dep_oran - ((1 / acilis_ms2) * 100):+.1f}%", "Durum": "✅ Değerli" if (dep_oran - ((1 / acilis_ms2) * 100)) > 0 else "❌ Değersiz"})

        if kapanis_ms1 is not None: value_verileri.append({"Bahis Tipi": "MS 1 (B365 Kapanış)", "Girdiğiniz Oran": kapanis_ms1, "Büro Olasılığı": f"% {(1 / kapanis_ms1) * 100:.1f}", "Gerçekleşen Olasılık": f"% {ev_oran:.1f}", "Sapma (Value)": f"{ev_oran - ((1 / kapanis_ms1) * 100):+.1f}%", "Durum": "✅ Değerli" if (ev_oran - ((1 / kapanis_ms1) * 100)) > 0 else "❌ Değersiz"})
        if kapanis_msx is not None: value_verileri.append({"Bahis Tipi": "MS X (B365 Kapanış)", "Girdiğiniz Oran": kapanis_msx, "Büro Olasılığı": f"% {(1 / kapanis_msx) * 100:.1f}", "Gerçekleşen Olasılık": f"% {ber_oran:.1f}", "Sapma (Value)": f"{ber_oran - ((1 / kapanis_msx) * 100):+.1f}%", "Durum": "✅ Değerli" if (ber_oran - ((1 / kapanis_msx) * 100)) > 0 else "❌ Değersiz"})
        if kapanis_ms2 is not None: value_verileri.append({"Bahis Tipi": "MS 2 (B365 Kapanış)", "Girdiğiniz Oran": kapanis_ms2, "Büro Olasılığı": f"% {(1 / kapanis_ms2) * 100:.1f}", "Gerçekleşen Olasılık": f"% {dep_oran:.1f}", "Sapma (Value)": f"{dep_oran - ((1 / kapanis_ms2) * 100):+.1f}%", "Durum": "✅ Değerli" if (dep_oran - ((1 / kapanis_ms2) * 100)) > 0 else "❌ Değersiz"})

        if kapanis_bf1 is not None: value_verileri.append({"Bahis Tipi": "MS 1 (Betfair)", "Girdiğiniz Oran": kapanis_bf1, "Büro Olasılığı": f"% {(1 / kapanis_bf1) * 100:.1f}", "Gerçekleşen Olasılık": f"% {ev_oran:.1f}", "Sapma (Value)": f"{ev_oran - ((1 / kapanis_bf1) * 100):+.1f}%", "Durum": "✅ Değerli" if (ev_oran - ((1 / kapanis_bf1) * 100)) > 0 else "❌ Değersiz"})
        if kapanis_bfx is not None: value_verileri.append({"Bahis Tipi": "MS X (Betfair)", "Girdiğiniz Oran": kapanis_bfx, "Büro Olasılığı": f"% {(1 / kapanis_bfx) * 100:.1f}", "Gerçekleşen Olasılık": f"% {ber_oran:.1f}", "Sapma (Value)": f"{ber_oran - ((1 / kapanis_bfx) * 100):+.1f}%", "Durum": "✅ Değerli" if (ber_oran - ((1 / kapanis_bfx) * 100)) > 0 else "❌ Değersiz"})
        if kapanis_bf2 is not None: value_verileri.append({"Bahis Tipi": "MS 2 (Betfair)", "Girdiğiniz Oran": kapanis_bf2, "Büro Olasılığı": f"% {(1 / kapanis_bf2) * 100:.1f}", "Gerçekleşen Olasılık": f"% {dep_oran:.1f}", "Sapma (Value)": f"{dep_oran - ((1 / kapanis_bf2) * 100):+.1f}%", "Durum": "✅ Değerli" if (dep_oran - ((1 / kapanis_bf2) * 100)) > 0 else "❌ Değersiz"})

        st.write("✅ CHECKPOINT 7: Value listesi oluşturuldu (henüz DataFrame'e çevrilmedi)")

        if value_verileri:
            st.markdown("#### 📈 Oran vs Gerçeklik Matrisi")
            value_df = pd.DataFrame(value_verileri)
            st.write("✅ CHECKPOINT 8: value_df oluşturuldu")
            st.dataframe(value_df, hide_index=True, width="stretch")
            st.write("✅ CHECKPOINT 9: value_df gösterildi")

        st.markdown("---")

        def skor_yap(h, a):
            if pd.isna(h) or pd.isna(a): return np.nan
            return f"{int(float(h))}-{int(float(a))}"

        if 'FTHG' in sonuclar.columns and 'FTAG' in sonuclar.columns:
            sonuclar['MS_Skor'] = sonuclar.apply(lambda row: skor_yap(row['FTHG'], row['FTAG']), axis=1)
            sonuclar['MS_Skor'] = sonuclar['MS_Skor'].astype("string")

        st.write("✅ CHECKPOINT 10: MS_Skor oluşturuldu")

        if 'HTHG' in sonuclar.columns and 'HTAG' in sonuclar.columns:
            sonuclar['İY_Skor'] = sonuclar.apply(lambda row: skor_yap(row['HTHG'], row['HTAG']), axis=1)
            sonuclar['İY_Skor'] = sonuclar['İY_Skor'].astype("string")

        st.write("✅ CHECKPOINT 11: İY_Skor oluşturuldu")

        gosterilecek_kolonlar = [
            'Lig', 'Date', 'HomeTeam', 'AwayTeam', 'İY_Skor', 'MS_Skor', 'FTR',
            'B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA', 'BFECH', 'BFECD', 'BFECA'
        ]
        mevcut_gosterim = [col for col in gosterilecek_kolonlar if col in sonuclar.columns]

        st.subheader("📋 Eşleşen Maçların Detay Listesi")
        st.write("✅ CHECKPOINT 12: Ana tablo gösterilmeden hemen önce")
        st.dataframe(sonuclar[mevcut_gosterim], width="stretch")
        st.write("✅ CHECKPOINT 13: Ana tablo gösterildi")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎯 İY Skorları")
            if 'İY_Skor' in sonuclar.columns:
                gecerli_iy = sonuclar['İY_Skor'].dropna()
                if not gecerli_iy.empty:
                    iy_frekans = gecerli_iy.value_counts()
                    iy_yuzde = gecerli_iy.value_counts(normalize=True) * 100
                    st.dataframe(pd.DataFrame({'Skor': iy_frekans.index, 'Tekrar': iy_frekans.values, '%': iy_yuzde.values.round(1)}), hide_index=True, width="stretch")
                else:
                    st.info("Veri yok.")

        st.write("✅ CHECKPOINT 14: İY skor tablosu gösterildi")

        with col2:
            st.subheader("🎯 MS Skorları")
            if 'MS_Skor' in sonuclar.columns:
                gecerli_ms = sonuclar['MS_Skor'].dropna()
                if not gecerli_ms.empty:
                    ms_frekans = gecerli_ms.value_counts()
                    ms_yuzde = gecerli_ms.value_counts(normalize=True) * 100
                    st.dataframe(pd.DataFrame({'Skor': ms_frekans.index, 'Tekrar': ms_frekans.values, '%': ms_yuzde.values.round(1)}), hide_index=True, width="stretch")
                else:
                    st.info("Veri yok.")

        st.write("✅ CHECKPOINT 15: MS skor tablosu gösterildi — TÜM SAYFA TAMAMLANDI")
    else:
        st.warning("Bu kombinasyona uyan maç bulunamadı.")

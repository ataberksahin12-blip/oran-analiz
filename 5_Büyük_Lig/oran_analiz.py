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
        'H_Avg': 'B365H', 'D_Avg': 'B365D', 'A_Avg': 'B365A',
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
                
            dataframes.append(gecici_df)
        except Exception as e:
            pass
            
    if len(dataframes) > 0:
        df = pd.concat(dataframes, ignore_index=True)
        
        if 'Lig' in df.columns:
            df['Lig'] = df['Lig'].astype(str).str.strip()
            df['Lig'] = df['Lig'].replace('WorldCupQualifiers', 'Dünya Kupası Elemeleri')
        
        df = df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'])
        
        if 'FTR' not in df.columns or df['FTR'].isnull().all():
            if 'FTHG' in df.columns and 'FTAG' in df.columns:
                conditions = [(df['FTHG'] > df['FTAG']), (df['FTHG'] == df['FTAG']), (df['FTHG'] < df['FTAG'])]
                choices = ['H', 'D', 'A']
                df['FTR'] = np.select(conditions, choices, default=np.nan)
                
        oran_sutunlari = ['B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA']
        for col in oran_sutunlari:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df
    return pd.DataFrame()

df = verileri_oku_v3()

if df.empty:
    st.error("Veriler okunamadı. Klasör yolunu kontrol et.")
else:
    st.sidebar.success(f"Toplam {len(df)} tekil maç yüklendi.")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌍 Lig Filtresi")
    mevcut_ligler = sorted(df['Lig'].dropna().unique().tolist()) if 'Lig' in df.columns else []
    secilen_ligler = st.sidebar.multiselect("Lig Seçin (Boş bırakırsanız tümü gelir)", mevcut_ligler)
    
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Oran Filtreleri")
    tolerans = st.sidebar.slider("Tolerans (Esneklik Payı)", min_value=0.00, max_value=0.50, value=0.03, step=0.01)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Açılış Oranları")
    acilis_ms1 = st.sidebar.number_input("MS 1 Açılış (B365H)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    acilis_msx = st.sidebar.number_input("MS X Açılış (B365D)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    acilis_ms2 = st.sidebar.number_input("MS 2 Açılış (B365A)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Kapanış Oranları")
    kapanis_ms1 = st.sidebar.number_input("MS 1 Kapanış (B365CH)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    kapanis_msx = st.sidebar.number_input("MS X Kapanış (B365CD)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    kapanis_ms2 = st.sidebar.number_input("MS 2 Kapanış (B365CA)", min_value=1.01, value=None, step=0.01, placeholder="Boş")

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

    st.subheader(f"📊 Kriterlere Uyan Toplam Maç Sayısı: {len(sonuclar)}")

    filtre_girildi_mi = any(v is not None for v in [acilis_ms1, acilis_msx, acilis_ms2, kapanis_ms1, kapanis_msx, kapanis_ms2])

    if not filtre_girildi_mi and not secilen_ligler:
        st.info("👈 Lütfen sol menüden lig veya oran girin.")
    elif len(sonuclar) > 0:
        
        # ==========================================
        # YENİ ADIM: HFA VE VALUE DEĞER ANALİZİ PANELİ
        # ==========================================
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
        
        # Metrik Kutuları
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Ev Sahibi Galibiyet %", f"% {ev_oran:.1f}")
        m_col2.metric("Beraberlik %", f"% {ber_oran:.1f}")
        m_col3.metric("Deplasman Galibiyet %", f"% {dep_oran:.1f}")
        m_col4.metric("HFA Gol Dominansı", f"+{hfa_gol_avantaji:.2f}" if hfa_gol_avantaji >= 0 else f"{hfa_gol_avantaji:.2f}")
        
        st.caption(f"**Saha Analizi:** Seçtiğiniz filtrelerde ev sahibi takımlar maç başına ortalama **{ort_ev_gol:.2f}** gol atarken, deplasman takımları **{ort_dep_gol:.2f}** gol atabilmiş.")
        
        # Girdilere Göre Dinamik Value Tablosu Oluşturma
        value_verileri = []
        
        # Açılış Oran Kontrolleri
        if acilis_ms1 is not None:
            kitapci_olasilik = (1 / acilis_ms1) * 100
            value = ev_oran - kitapci_olasilik
            value_verileri.append({"Bahis Tipi": "MS 1 (Açılış)", "Girdiğiniz Oran": acilis_ms1, "Büro Olasılığı": f"% {kitapci_olasilik:.1f}", "Gerçekleşen Olasılık": f"% {ev_oran:.1f}", "Sapma (Value)": f"{value:+.1f}%", "Durum": "✅ Değerli" if value > 0 else "❌ Değersiz"})
            
        if acilis_msx is not None:
            kitapci_olasilik = (1 / acilis_msx) * 100
            value = ber_oran - kitapci_olasilik
            value_verileri.append({"Bahis Tipi": "MS X (Açılış)", "Girdiğiniz Oran": acilis_msx, "Büro Olasılığı": f"% {kitapci_olasilik:.1f}", "Gerçekleşen Olasılık": f"% {ber_oran:.1f}", "Sapma (Value)": f"{value:+.1f}%", "Durum": "✅ Değerli" if value > 0 else "❌ Değersiz"})
            
        if acilis_ms2 is not None:
            kitapci_olasilik = (1 / acilis_ms2) * 100
            value = dep_oran - kitapci_olasilik
            value_verileri.append({"Bahis Tipi": "MS 2 (Açılış)", "Girdiğiniz Oran": acilis_ms2, "Büro Olasılığı": f"% {kitapci_olasilik:.1f}", "Gerçekleşen Olasılık": f"% {dep_oran:.1f}", "Sapma (Value)": f"{value:+.1f}%", "Durum": "✅ Değerli" if value > 0 else "❌ Değersiz"})

        # Kapanış Oran Kontrolleri
        if kapanis_ms1 is not None:
            kitapci_olasilik = (1 / kapanis_ms1) * 100
            value = ev_oran - kitapci_olasilik
            value_verileri.append({"Bahis Tipi": "MS 1 (Kapanış)", "Girdiğiniz Oran": kapanis_ms1, "Büro Olasılığı": f"% {kitapci_olasilik:.1f}", "Gerçekleşen Olasılık": f"% {ev_oran:.1f}", "Sapma (Value)": f"{value:+.1f}%", "Durum": "✅ Değerli" if value > 0 else "❌ Değersiz"})
            
        if kapanis_msx is not None:
            kitapci_olasilik = (1 / kapanis_msx) * 100
            value = ber_oran - kitapci_olasilik
            value_verileri.append({"Bahis Tipi": "MS X (Kapanış)", "Girdiğiniz Oran": kapanis_msx, "Büro Olasılığı": f"% {kitapci_olasilik:.1f}", "Gerçekleşen Olasılık": f"% {ber_oran:.1f}", "Sapma (Value)": f"{value:+.1f}%", "Durum": "✅ Değerli" if value > 0 else "❌ Değersiz"})
            
        if kapanis_ms2 is not None:
            kitapci_olasilik = (1 / kapanis_ms2) * 100
            value = dep_oran - kitapci_olasilik
            value_verileri.append({"Bahis Tipi": "MS 2 (Kapanış)", "Girdiğiniz Oran": kapanis_ms2, "Büro Olasılığı": f"% {kitapci_olasilik:.1f}", "Gerçekleşen Olasılık": f"% {dep_oran:.1f}", "Sapma (Value)": f"{value:+.1f}%", "Durum": "✅ Değerli" if value > 0 else "❌ Değersiz"})
            
        if value_verileri:
            st.markdown("#### 📈 Oran vs Gerçeklik Matrisi")
            value_df = pd.DataFrame(value_verileri)
            st.dataframe(value_df, hide_index=True, use_container_width=True)
            
        st.markdown("---")
        # ==========================================

        def skor_yap(h, a):
            if pd.isna(h) or pd.isna(a): return np.nan
            return f"{int(float(h))}-{int(float(a))}"

        if 'FTHG' in sonuclar.columns and 'FTAG' in sonuclar.columns:
            sonuclar['MS_Skor'] = sonuclar.apply(lambda row: skor_yap(row['FTHG'], row['FTAG']), axis=1)

        if 'HTHG' in sonuclar.columns and 'HTAG' in sonuclar.columns:
            sonuclar['İY_Skor'] = sonuclar.apply(lambda row: skor_yap(row['HTHG'], row['HTAG']), axis=1)
        
        gosterilecek_kolonlar = [
            'Lig', 'Date', 'HomeTeam', 'AwayTeam', 'İY_Skor', 'MS_Skor', 'FTR',
            'B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA'
        ]
        mevcut_gosterim = [col for col in gosterilecek_kolonlar if col in sonuclar.columns]
        
        st.subheader("📋 Eşleşen Maçların Detay Listesi")
        st.dataframe(sonuclar[mevcut_gosterim], use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎯 İY Skorları")
            if 'İY_Skor' in sonuclar.columns:
                gecerli_iy = sonuclar['İY_Skor'].dropna()
                if not gecerli_iy.empty:
                    iy_frekans = gecerli_iy.value_counts()
                    iy_yuzde = gecerli_iy.value_counts(normalize=True) * 100
                    st.dataframe(pd.DataFrame({'Skor': iy_frekans.index, 'Tekrar': iy_frekans.values, '%': iy_yuzde.values.round(1)}), hide_index=True, use_container_width=True)
                else:
                    st.info("Veri yok.")
            
        with col2:
            st.subheader("🎯 MS Skorları")
            if 'MS_Skor' in sonuclar.columns:
                gecerli_ms = sonuclar['MS_Skor'].dropna()
                if not gecerli_ms.empty:
                    ms_frekans = gecerli_ms.value_counts()
                    ms_yuzde = gecerli_ms.value_counts(normalize=True) * 100
                    st.dataframe(pd.DataFrame({'Skor': ms_frekans.index, 'Tekrar': ms_frekans.values, '%': ms_yuzde.values.round(1)}), hide_index=True, use_container_width=True)
                else:
                    st.info("Veri yok.")
    else:
        st.warning("Bu kombinasyona uyan maç bulunamadı.")

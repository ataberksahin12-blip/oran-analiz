import streamlit as st
import pandas as pd
import glob
import os
import numpy as np

# Sayfa Yapılandırması
st.set_page_config(page_title="Oran Analiz Paneli", layout="wide")
st.title("⚽ Gelişmiş Futbol Oran Analizörü")

@st.cache_data
def verileri_oku_v2():
    # Bütün CSV'leri bul (İçeride çift dosyalar olsa bile)
    tum_dosyalar = glob.glob("**/*.csv", recursive=True)
    dataframes = []
    
    # Sütun isimlerini eşitleme sözlüğü
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
        
        # LİG İSİMLERİ TEMİZLİĞİ
        if 'Lig' in df.columns:
            df['Lig'] = df['Lig'].astype(str).str.strip()
            df['Lig'] = df['Lig'].replace('WorldCupQualifiers', 'Dünya Kupası Elemeleri')
        
        # --- ZIRH 1: ÇİFT YÜKLENEN DOSYALARI SİL (37 BİN MAÇ DÜZELTMESİ) ---
        # Aynı tarih ve aynı takımların oynadığı maçları teke düşürür.
        df = df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'])
        
        # FTR (Maç Sonucu 1-X-2) Hesaplama
        if 'FTR' not in df.columns or df['FTR'].isnull().all():
            if 'FTHG' in df.columns and 'FTAG' in df.columns:
                conditions = [
                    (df['FTHG'] > df['FTAG']),
                    (df['FTHG'] == df['FTAG']),
                    (df['FTHG'] < df['FTAG'])
                ]
                choices = ['H', 'D', 'A']
                df['FTR'] = np.select(conditions, choices, default=np.nan)
                
        # Oranları güvenli sayıya çevirme
        oran_sutunlari = ['B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA']
        for col in oran_sutunlari:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df
    return pd.DataFrame()

df = verileri_oku_v2()

if df.empty:
    st.error("Veriler okunamadı. Klasör yolunu kontrol et.")
else:
    st.sidebar.success(f"Toplam {len(df)} tekil maç yüklendi.")
    with st.sidebar.expander("📂 Okunan Dosyalar", expanded=False):
        st.dataframe(df['Source_File'].value_counts())
        
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("🌍 Lig Filtresi")
    mevcut_ligler = sorted(df['Lig'].dropna().unique().tolist()) if 'Lig' in df.columns else []
    secilen_ligler = st.sidebar.multiselect("Lig Seçin (Boş bırakırsanız tümü gelir)", mevcut_ligler)
    
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Oran Filtreleri")
    st.sidebar.caption("İstemediğiniz oranları boş bırakın.")
    
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

    # Lig Filtrelemesi
    if secilen_ligler and 'Lig' in sonuclar.columns:
        sonuclar = sonuclar[sonuclar['Lig'].isin(secilen_ligler)]

    # Açılış Filtreleri
    if acilis_ms1 is not None and 'B365H' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365H'])
        sonuclar = sonuclar[sonuclar['B365H'].between(acilis_ms1 - tolerans, acilis_ms1 + tolerans)]
        
    if acilis_msx is not None and 'B365D' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365D'])
        sonuclar = sonuclar[sonuclar['B365D'].between(acilis_msx - tolerans, acilis_msx + tolerans)]
        
    if acilis_ms2 is not None and 'B365A' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365A'])
        sonuclar = sonuclar[sonuclar['B365A'].between(acilis_ms2 - tolerans, acilis_ms2 + tolerans)]

    # Kapanış Filtreleri
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
        
        # --- ZIRH 2: ÇÖKMEYİ ENGELLEYEN GÜVENLİ SKOR OLUŞTURUCU ---
        # Sadece gol verisi olan satırlar için skor hesaplar, geri kalanını atlar
        if 'FTHG' in sonuclar.columns and 'FTAG' in sonuclar.columns:
            gecerli_ms = sonuclar.dropna(subset=['FTHG', 'FTAG'])
            sonuclar.loc[gecerli_ms.index, 'MS_Skor'] = gecerli_ms['FTHG'].astype(str).str.split('.').str[0] + "-" + gecerli_ms['FTAG'].astype(str).str.split('.').str[0]

        if 'HTHG' in sonuclar.columns and 'HTAG' in sonuclar.columns:
            gecerli_iy = sonuclar.dropna(subset=['HTHG', 'HTAG'])
            sonuclar.loc[gecerli_iy.index, 'İY_Skor'] = gecerli_iy['HTHG'].astype(str).str.split('.').str[0] + "-" + gecerli_iy['HTAG'].astype(str).str.split('.').str[0]
        
        gosterilecek_kolonlar = [
            'Lig', 'Date', 'HomeTeam', 'AwayTeam', 'İY_Skor', 'MS_Skor', 'FTR',
            'B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA'
        ]
        mevcut_gosterim = [col for col in gosterilecek_kolonlar if col in sonuclar.columns]
        
        st.dataframe(sonuclar[mevcut_gosterim], use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎯 En Sık Görülen İY Skorları")
            if 'İY_Skor' in sonuclar.columns:
                gecerli_iy = sonuclar[sonuclar['İY_Skor'].str.contains('nan', na=False) == False]['İY_Skor'].dropna()
                if not gecerli_iy.empty:
                    iy_frekans = gecerli_iy.value_counts()
                    iy_yuzde = gecerli_iy.value_counts(normalize=True) * 100
                    iy_tablo = pd.DataFrame({'Skor': iy_frekans.index, 'Tekrar': iy_frekans.values, '%': iy_yuzde.values.round(1)})
                    st.dataframe(iy_tablo, hide_index=True, use_container_width=True)
                else:
                    st.info("Bu filtrelere ait İlk Yarı skoru verisi bulunamadı.")
            
        with col2:
            st.subheader("🎯 En Sık Görülen MS Skorları")
            if 'MS_Skor' in sonuclar.columns:
                gecerli_ms = sonuclar[sonuclar['MS_Skor'].str.contains('nan', na=False) == False]['MS_Skor'].dropna()
                if not gecerli_ms.empty:
                    ms_frekans = gecerli_ms.value_counts()
                    ms_yuzde = gecerli_ms.value_counts(normalize=True) * 100
                    ms_tablo = pd.DataFrame({'Skor': ms_frekans.index, 'Tekrar': ms_frekans.values, '%': ms_yuzde.values.round(1)})
                    st.dataframe(ms_tablo, hide_index=True, use_container_width=True)
                else:
                    st.info("Bu filtrelere ait Maç Sonucu skoru verisi bulunamadı.")
    else:
        st.warning("Bu kombinasyona uyan maç bulunamadı.")
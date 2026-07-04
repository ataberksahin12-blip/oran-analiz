import streamlit as st
import pandas as pd
import glob
import os
import numpy as np

# Sayfa Yapılandırması
st.set_page_config(page_title="Oran Analiz Paneli", layout="wide")
st.title("⚽ Gelişmiş Futbol Oran Analizörü")

@st.cache_data
def load_data():
    klasor_yolu = "5_Büyük_Lig"
    tum_dosyalar = glob.glob(os.path.join(klasor_yolu, "*.csv"))
    dataframes = []
    
    # Sütun isimlerini eşitleme sözlüğü
        # Sütun isimlerini eşitleme sözlüğü
    sutun_degisimleri = {
        'Home': 'HomeTeam', 'Away': 'AwayTeam',
        'HGFT': 'FTHG', 'AGFT': 'FTAG',
        'HG1st': 'HTHG', 'AG1st': 'HTAG',
        'bet365-H': 'B365H', 'bet365-D': 'B365D', 'bet365-A': 'B365A',
        'HG': 'FTHG', 'AG': 'FTAG', 'Res': 'FTR'
    }

    
    for dosya in tum_dosyalar:
        try:
            dosya_adi = os.path.basename(dosya)
            if 'WorldCup' in dosya_adi:
                gecici_df = pd.read_csv(dosya, encoding='latin1', sep=';')
            else:
                gecici_df = pd.read_csv(dosya, encoding='latin1')
                
            # İsimleri standartlaştır ve boşlukları sil
            gecici_df.rename(columns=sutun_degisimleri, inplace=True)
            gecici_df.columns = gecici_df.columns.str.replace(' ', '')
            gecici_df['Source_File'] = dosya_adi
            dataframes.append(gecici_df)
        except Exception as e:
            pass
            
    if len(dataframes) > 0:
        df = pd.concat(dataframes, ignore_index=True)
        
        # --- ZIRH 1: FTR (Maç Sonucu 1-X-2) EKSİKSE KENDİN HESAPLA ---
        if 'FTR' not in df.columns or df['FTR'].isnull().all():
            if 'FTHG' in df.columns and 'FTAG' in df.columns:
                conditions = [
                    (df['FTHG'] > df['FTAG']),
                    (df['FTHG'] == df['FTAG']),
                    (df['FTHG'] < df['FTAG'])
                ]
                choices = ['H', 'D', 'A'] # H: Home, D: Draw, A: Away
                df['FTR'] = np.select(conditions, choices, default=np.nan)
                
        # --- ZIRH 2: ORANLARI KESİN SAYIYA (FLOAT) ÇEVİR ---
        oran_sutunlari = ['B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA']
        for col in oran_sutunlari:
            if col in df.columns:
                # Eğer içinde virgül varsa noktaya çevir
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df
    return pd.DataFrame()

# Veriyi Yükle
df = load_data()

if df.empty:
    st.error("Veriler okunamadı. Klasör yolunu kontrol et.")
else:
    # --- YENİ: VERİ RÖNTGENİ (Sol Menüde) ---
    st.sidebar.success(f"Toplam {len(df)} maç yüklendi.")
    with st.sidebar.expander("📂 Okunan Dosyalar ve Maç Sayıları", expanded=False):
        st.dataframe(df['Source_File'].value_counts())
        
    st.sidebar.markdown("---")
    
    # --- FİLTRELEME ALANI ---
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

    st.sidebar.markdown("---")
    st.sidebar.subheader("2.5 Alt / Üst Oranları")
    acilis_ust = st.sidebar.number_input("2.5 Üst Açılış (B365>2.5)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    kapanis_ust = st.sidebar.number_input("2.5 Üst Kapanış (B365C>2.5)", min_value=1.01, value=None, step=0.01, placeholder="Boş")
    # --- DİNAMİK FİLTRELEME MANTIĞI ---
    sonuclar = df.copy()

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

    if acilis_ust is not None and 'B365>2.5' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365>2.5'])
        sonuclar = sonuclar[sonuclar['B365>2.5'].between(acilis_ust - tolerans, acilis_ust + tolerans)]

    if kapanis_ust is not None and 'B365C>2.5' in sonuclar.columns:
        sonuclar = sonuclar.dropna(subset=['B365C>2.5'])
        sonuclar = sonuclar[sonuclar['B365C>2.5'].between(kapanis_ust - tolerans, kapanis_ust + tolerans)]

    # --- SONUÇLARI EKRANA BASMA ---
    st.subheader(f"📊 Kriterlere Uyan Toplam Maç Sayısı: {len(sonuclar)}")

    filtre_girildi_mi = any(v is not None for v in [acilis_ms1, acilis_msx, acilis_ms2, kapanis_ms1, kapanis_msx, kapanis_ms2])

    if not filtre_girildi_mi:
        st.info("👈 Lütfen sol menüden oranları girin. İstemediğiniz oranları boş bırakın.")
    elif len(sonuclar) > 0:
        if 'HTHG' in sonuclar.columns and 'FTHG' in sonuclar.columns:
            sonuclar['İY_Skor'] = sonuclar['HTHG'].astype(str).str.split('.').str[0] + "-" + sonuclar['HTAG'].astype(str).str.split('.').str[0]
            sonuclar['MS_Skor'] = sonuclar['FTHG'].astype(str).str.split('.').str[0] + "-" + sonuclar['FTAG'].astype(str).str.split('.').str[0]
        
        gosterilecek_kolonlar = [
            'Date', 'Source_File', 'HomeTeam', 'AwayTeam', 'İY_Skor', 'MS_Skor', 'FTR',
            'B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA'
        ]
        mevcut_gosterim = [col for col in gosterilecek_kolonlar if col in sonuclar.columns]
        
        st.dataframe(sonuclar[mevcut_gosterim], use_container_width=True)
        
        # --- İY VE MS SKOR DAĞILIMLARI (GRAFİK YERİNE TABLO) ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 En Sık Görülen İY Skorları")
            if 'İY_Skor' in sonuclar.columns:
                # Sadece maçların oynandığı ve skorların girildiği verileri filtrele
                gecerli_iy = sonuclar[sonuclar['İY_Skor'].str.contains('nan', na=False) == False]['İY_Skor']
                
                if not gecerli_iy.empty:
                    iy_frekans = gecerli_iy.value_counts()
                    iy_yuzde = gecerli_iy.value_counts(normalize=True) * 100
                    
                    iy_tablo = pd.DataFrame({
                        'Skor': iy_frekans.index,
                        'Tekrar Sayısı': iy_frekans.values,
                        'Yüzde (%)': iy_yuzde.values.round(1)
                    })
                    
                    st.dataframe(iy_tablo, hide_index=True, use_container_width=True)
                else:
                    st.info("Geçerli İlk Yarı skoru bulunamadı.")
            
        with col2:
            st.subheader("🎯 En Sık Görülen MS Skorları")
            if 'MS_Skor' in sonuclar.columns:
                # Skoru eksik (nan) olmayanları filtrele
                gecerli_ms = sonuclar[sonuclar['MS_Skor'].str.contains('nan', na=False) == False]['MS_Skor']
                
                if not gecerli_ms.empty:
                    ms_frekans = gecerli_ms.value_counts()
                    ms_yuzde = gecerli_ms.value_counts(normalize=True) * 100
                    
                    ms_tablo = pd.DataFrame({
                        'Skor': ms_frekans.index,
                        'Tekrar Sayısı': ms_frekans.values,
                        'Yüzde (%)': ms_yuzde.values.round(1)
                    })
                    
                    st.dataframe(ms_tablo, hide_index=True, use_container_width=True)
                else:
                    st.info("Geçerli Maç Sonucu skoru bulunamadı.")
    else:
        st.warning("Bu kombinasyona uyan geçmiş maç bulunamadı. Toleransı artırabilirsiniz.")

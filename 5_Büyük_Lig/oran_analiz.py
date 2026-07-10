import streamlit as st
import pandas as pd
import glob
import os
import numpy as np
import gc  # RAM temizliği için Garbage Collector

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

    hedef_sutunlar = [
        'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HTHG', 'HTAG',
        'B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA', 
        'BFECH', 'BFECD', 'BFECA', 'FTR', 'Lig', 'Source_File', 'Country'
    ]
    
    for dosya in tum_dosyalar:
        try:
            dosya_adi = os.path.basename(dosya)
            if 'WorldCup' in dosya_adi:
                gecici_df = pd.read_csv(dosya, encoding='latin1', sep=';')
            else:
                gecici_df = pd.read_csv(dosya, encoding='latin1')
                
            gecici_df.rename(columns=sutun_degisimleri, inplace=True)
            gecici_df.columns = gecici_df.columns.str.replace(' ', '')
            
            yeni_kolonlar = {'Source_File': dosya_adi}
            if 'Lig' not in gecici_df.columns:
                yeni_kolonlar['Lig'] = dosya_adi.replace('.csv', '')
                
            gecici_df = gecici_df.assign(**yeni_kolonlar)
            
            mevcut_hedefler = [col for col in hedef_sutunlar if col in gecici_df.columns]
            gecici_df = gecici_df[mevcut_hedefler].copy()
            
            # --- YENİ: VERİ TİPİ (RAM) OPTİMİZASYONU ---
            # Sayısal verileri 64-bit'ten 32-bit'e düşür
            sayisal_kolonlar = ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA', 'BFECH', 'BFECD', 'BFECA']
            for col in sayisal_kolonlar:
                if col in gecici_df.columns:
                    if gecici_df[col].dtype == object:
                        gecici_df[col] = gecici_df[col].astype(str).str.replace(',', '.')
                    gecici_df[col] = pd.to_numeric(gecici_df[col], errors='coerce').astype('float32') # RAM kullanımını yarıya indirir
            
            # Metin verilerini category (kategori) tipine çevir
            kategori_kolonlar = ['HomeTeam', 'AwayTeam', 'FTR', 'Lig', 'Country']
            for col in kategori_kolonlar:
                if col in gecici_df.columns:
                    gecici_df[col] = gecici_df[col].astype('category') # Tekrar eden metinlerin RAM'i şişirmesini engeller

            dataframes.append(gecici_df)
        except Exception as e:
            pass
            
    if len(dataframes) > 0:
        df = pd.concat(dataframes, ignore_index=True)
        
        # Geçici listeyi bellekten sil ve çöp toplayıcıyı çalıştır
        del dataframes
        gc.collect() 
        
        # --- LİG İSİMLERİNİ TEMİZLEME VE BİRLEŞTİRME ---
        if 'Lig' in df.columns:
            # İşlemlerden önce kategoriyi metne çevirip, işlem bitince tekrar kategori yapıyoruz
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
            df['Lig'] = df['Lig'].replace(lig_isimleri).astype('category')
        
        df = df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'])
        
        if 'FTR' not in df.columns:
            df['FTR'] = np.nan
            
        if 'FTHG' in df.columns and 'FTAG' in df.columns:
            eksik_ftr = df['FTR'].isnull()
            df.loc[eksik_ftr & (df['FTHG'] > df['FTAG']), 'FTR'] = 'H'
            df.loc[eksik_ftr & (df['FTHG'] == df['FTAG']), 'FTR'] = 'D'
            df.loc[eksik_ftr & (df['FTHG'] < df['FTAG']), 'FTR'] = 'A'
            df['FTR'] = df['FTR'].astype('category') # FTR kolonunu da optimize et
                
        return df
    return pd.DataFrame()

@st.cache_data
def verileri_oku_v3():
    tum_dosyalar = glob.glob("**/*.csv", recursive=True)
    dataframes = []
    
    # Sadece saf Bet365 oranlarına odaklanan yapı
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
                
            dataframes.append(gecici_df)
        except Exception as e:
            pass
            
    if len(dataframes) > 0:
        df = pd.concat(dataframes, ignore_index=True)
        
        # --- LİG İSİMLERİNİ TEMİZLEME VE BİRLEŞTİRME BLOKU ---
        if 'Lig' in df.columns:
            df['Lig'] = df['Lig'].astype(str).str.strip()
            
            # 1. Dosya isimlerinden gelen "(1)", "(2)" gibi Windows kopya eklerini temizle
            df['Lig'] = df['Lig'].str.replace(r'\s*\(\d+\)', '', regex=True)
            
            # 2. Yıllara göre ayrılan Dünya Kupası turnuvalarını tek çatıda topla (2014, 2018, 2022 -> Dünya Kupası)
            df.loc[df['Lig'].str.contains('World Cup', case=False, na=False) & ~df['Lig'].str.contains('Qualifiers', case=False, na=False), 'Lig'] = 'Dünya Kupası'
            df['Lig'] = df['Lig'].replace('WorldCupQualifiers', 'Dünya Kupası Elemeleri')
            
            # 3. football-data.co.uk'un anlamsız lig kodlarını gerçek isimlere çevir
            lig_isimleri = {
                'E0': 'Premier League (İngiltere)',
                'E1': 'Championship (İngiltere)',
                'E2': 'League 1 (İngiltere)',
                'E3': 'League 2 (İngiltere)',
                'EC': 'National League (İngiltere)',
                'SC0': 'Scottish Premiership',
                'D1': 'Bundesliga (Almanya)',
                'D2': '2. Bundesliga (Almanya)',
                'I1': 'Serie A (İtalya)',
                'I2': 'Serie B (İtalya)',
                'SP1': 'La Liga (İspanya)',
                'SP2': 'Segunda Division (İspanya)',
                'F1': 'Ligue 1 (Fransa)',
                'F2': 'Ligue 2 (Fransa)',
                'N1': 'Eredivisie (Hollanda)',
                'B1': 'Pro League (Belçika)',
                'P1': 'Primeira Liga (Portekiz)',
                'T1': 'Süper Lig (Türkiye)',
                'G1': 'Super League (Yunanistan)',
                'WorldCup': 'Dünya Kupası'
            }
            df['Lig'] = df['Lig'].replace(lig_isimleri)
        # --------------------------------------------------
        
        df = df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'])
        
        if 'FTR' not in df.columns:
            df['FTR'] = np.nan
            
        if 'FTHG' in df.columns and 'FTAG' in df.columns:
            eksik_ftr = df['FTR'].isnull()
            df.loc[eksik_ftr & (df['FTHG'] > df['FTAG']), 'FTR'] = 'H'
            df.loc[eksik_ftr & (df['FTHG'] == df['FTAG']), 'FTR'] = 'D'
            df.loc[eksik_ftr & (df['FTHG'] < df['FTAG']), 'FTR'] = 'A'
                
        oran_sutunlari = ['B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA']
        for col in oran_sutunlari:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df
    return pd.DataFrame()

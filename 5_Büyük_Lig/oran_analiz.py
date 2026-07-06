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
        
        # --- YENİ EKLENEN VE DÜZELTİLEN BLOK BURASI ---
        if 'FTR' not in df.columns:
            df['FTR'] = np.nan
            
        if 'FTHG' in df.columns and 'FTAG' in df.columns:
            eksik_ftr = df['FTR'].isnull()
            df.loc[eksik_ftr & (df['FTHG'] > df['FTAG']), 'FTR'] = 'H'
            df.loc[eksik_ftr & (df['FTHG'] == df['FTAG']), 'FTR'] = 'D'
            df.loc[eksik_ftr & (df['FTHG'] < df['FTAG']), 'FTR'] = 'A'
        # ----------------------------------------------
                
        oran_sutunlari = ['B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA']
        for col in oran_sutunlari:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df
    return pd.DataFrame()

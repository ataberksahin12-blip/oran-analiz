# Eğer FTR kolonu hiç yoksa önce boş olarak oluştur
        if 'FTR' not in df.columns:
            df['FTR'] = np.nan
            
        # Sadece FTR'si eksik olan ama atılan/yenilen gol verisi olan satırları bul ve H, D, A olarak doldur
        if 'FTHG' in df.columns and 'FTAG' in df.columns:
            eksik_ftr = df['FTR'].isnull()
            df.loc[eksik_ftr & (df['FTHG'] > df['FTAG']), 'FTR'] = 'H'
            df.loc[eksik_ftr & (df['FTHG'] == df['FTAG']), 'FTR'] = 'D'
            df.loc[eksik_ftr & (df['FTHG'] < df['FTAG']), 'FTR'] = 'A'

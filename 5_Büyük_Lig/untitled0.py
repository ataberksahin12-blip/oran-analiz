import pandas as pd
import glob
import os

# 1. Klasörün bilgisayarındaki TAM yolunu buraya yazmalısın.
# Örnek: Masaüstündeyse r"C:\Users\ataberk\Desktop\5_Büyük_Lig" şeklinde olmalı.
klasor_yolu = r"C:\Users\Ataberk\Desktop\5_Büyük_Lig"

tum_dosyalar = glob.glob(os.path.join(klasor_yolu, "*.csv"))
dataframes = []

print("Processing files in the directory...")

for dosya in tum_dosyalar:
    try:
        df = pd.read_csv(dosya, encoding='latin1')
        df['Source_File'] = os.path.basename(dosya)
        dataframes.append(df)
        print(f"Successfully loaded: {os.path.basename(dosya)}")
    except Exception as e:
        print(f"Error reading {os.path.basename(dosya)}: {e}")

# 2. Hata almamak için master_df'i önceden boş olarak tanımlıyoruz
master_df = pd.DataFrame()

if dataframes:
    master_df = pd.concat(dataframes, ignore_index=True)
    print(f"\nSuccess! Master database created with {len(master_df)} matches.")
else:
    print(f"\nHATA: '{klasor_yolu}' konumunda hiç CSV dosyası bulunamadı!")
    print("Lütfen klasör yolunun doğruluğunu kontrol edin.")

# 3. FİLTRELEME MANTIĞI (Sadece master_df boş değilse çalışır)
if not master_df.empty:
    hedef_acilis_ms1 = 1.55   
    hedef_kapanis_ms1 = 1.43  
    tolerans = 0.03

    acilis_sutunu = 'B365H'
    kapanis_sutunu = 'B365CH'

    if acilis_sutunu in master_df.columns and kapanis_sutunu in master_df.columns:
        analiz_df = master_df.dropna(subset=[acilis_sutunu, kapanis_sutunu])
        
        sonuclar = analiz_df[
            (analiz_df[acilis_sutunu].between(hedef_acilis_ms1 - tolerans, hedef_acilis_ms1 + tolerans)) &
            (analiz_df[kapanis_sutunu].between(hedef_kapanis_ms1 - tolerans, hedef_kapanis_ms1 + tolerans))
        ]
        
        print(f"\nTotal matching matches found: {len(sonuclar)}")
        
        if len(sonuclar) > 0:
            gosterilecekler = ['Date', 'Source_File', 'HomeTeam', 'AwayTeam', 'HTHG', 'HTAG', 'FTHG', 'FTAG', 'FTR']
            mevcut_sutunlar = [col for col in gosterilecekler if col in sonuclar.columns]
            
            print("\n--- MATCHING RECORDS ---")
            print(sonuclar[mevcut_sutunlar].head(20))
    else:
        print(f"\nRequired columns ({acilis_sutunu} or {kapanis_sutunu}) not found in the database.")
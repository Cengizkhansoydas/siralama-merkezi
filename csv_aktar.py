import sqlite3
import pandas as pd
import os

def toplu_csv_aktar():
    # 🎯 HEDEF TAM NOKTA: Statik klasörünün içindeki data dizini
    klasor = os.path.join('static', 'data')
    
    if not os.path.exists(klasor):
        print(f"Hata: '{klasor}' klasörü bulunamadı!")
        return
        
    print(f"📂 Veriler '{klasor}' klasöründen okunuyor...\n")
        
    ders_matrisi = {
        'tyt_turkce.csv': 'yks_konu_tyt_turkce',
        'tyt_matematik.csv': 'yks_konu_tyt_matematik',
        'tyt_geometri.csv': 'yks_konu_tyt_geometri',
        'tyt_fizik.csv': 'yks_konu_tyt_fizik',
        'tyt_kimya.csv': 'yks_konu_tyt_kimya',
        'tyt_biyoloji.csv': 'yks_konu_tyt_biyoloji',
        'tyt_tarih.csv': 'yks_konu_tyt_tarih',
        'tyt_cografya.csv': 'yks_konu_tyt_cografya',
        'tyt_felsefe.csv': 'yks_konu_tyt_felsefe',
        'tyt_din.csv': 'yks_konu_tyt_din',
        'ayt_matematik.csv': 'yks_konu_ayt_matematik',
        'ayt_geometri.csv': 'yks_konu_ayt_geometri',
        'ayt_edebiyat.csv': 'yks_konu_ayt_edebiyat',
        'ayt_fizik.csv': 'yks_konu_ayt_fizik',
        'ayt_kimya.csv': 'yks_konu_ayt_kimya',
        'ayt_biyoloji.csv': 'yks_konu_ayt_biyoloji',
        'ayt_tarih.csv': 'yks_konu_ayt_tarih',
        'ayt_cografya.csv': 'yks_konu_ayt_cografya',
        'ayt_felsefe.csv': 'yks_konu_ayt_felsefe',
        'ayt_din.csv': 'yks_konu_ayt_din'
    }
    
    conn = sqlite3.connect('veritabani.db')
    aktarilan_sayisi = 0
    
    for csv_adi, tablo_adi in ders_matrisi.items():
        tam_yol = os.path.join(klasor, csv_adi)
        if os.path.exists(tam_yol):
            try:
                with open(tam_yol, 'r', encoding='utf-8') as f:
                    ilk_satir = f.readline()
                    ayirici = ';' if ';' in ilk_satir else ','
                
                df = pd.read_csv(tam_yol, sep=ayirici)
                df.to_sql(tablo_adi, conn, if_exists='replace', index=False)
                print(f"✅ {csv_adi} -> veritabanına '{tablo_adi}' olarak işlendi.")
                aktarilan_sayisi += 1
            except Exception as e:
                print(f"❌ {csv_adi} aktarılırken hata oluştu: {str(e)}")
        else:
            print(f"⚠️ Dosya bulunamadı: {tam_yol}")
                
    conn.close()
    print(f"\n🎉 Toplam {aktarilan_sayisi} dersin soru dağılımı başarıyla veritabanına yüklendi!")

if __name__ == '__main__':
    toplu_csv_aktar()
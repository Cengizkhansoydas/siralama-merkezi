import pandas as pd
import sqlite3
import os

def tum_verileri_tabana_aktar():
    klasor_yolu = 'yks_verileri'
    db_yolu = 'veritabani.db'
    
    if not os.path.exists(klasor_yolu):
        print(f"❌ HATA: '{klasor_yolu}' klasörü bulunamadı!")
        return

    # Sadece .xlsx dosyalarını alıyoruz
    excel_dosyalari = [f for f in os.listdir(klasor_yolu) if f.endswith('.xlsx')]

    if not excel_dosyalari:
        print(f"❌ HATA: '{klasor_yolu}' klasöründe hiç Excel (.xlsx) dosyası bulunamadı!")
        return

    print(f"🔍 Toplam {len(excel_dosyalari)} adet Excel dosyası tespit edildi.")
    
    # index.html şablonuyla birebir uyumlu 8 sütunlu standart düzen
    standart_sutunlar = [
        "Üniversite", 
        "Bölüm", 
        "Puan Türü", 
        "Yıl", 
        "Kontenjan", 
        "Yerleşen", 
        "Puan", 
        "Sıralama"
    ]
    
    # Excel dosyalarındaki farklı sütun isimlerini yakalayan güncel akıllı sözlük
    eslesme_sozlugu = {
        "Üniversite": ['üniversite', 'universite', 'uni', 'universite_adi', 'üniversite adı', 'okul', 'universite adi', 'üniversite adı'],
        "Bölüm": ['bölüm', 'bolum', 'program', 'program_adi', 'bölüm adı', 'program adı', 'program adi'],
        "Puan Türü": ['puan türü', 'puan_turu', 'tür', 'puan_tipi', 'kontenjan türü', 'puan turu', 'puan tür', 'p.türü'],
        "Yıl": ['yıl', 'yil', 'tercih yılı', 'sene', 'tercih_yili', 'tercih yili'],
        
        # 🎯 Noktalı halleri buraya ekledik:
        "Kontenjan": ['kontenjan', 'kont', 'kont.', 'kont_sayisi', 'genel kontenjan', 'kontenjanı', 'kontenjani'],
        "Yerleşen": ['yerleşen', 'yerlesen', 'yer.', 'yerlesen_sayisi', 'yerlesme_orani', 'yerlesen sayisi'],
        
        "Puan": ['puan', 'taban puan', 'taban_puan', 'taban puanı', 'puanı', 'en küçük puan', 'taban puani', 'puani', 'puan_degeri'],
        "Sıralama": ['sıralama', 'siralar', 'siralamalar', 'siralama', 'başarı sırası', 'basari sirasi', 'başarı sıralaması', 'en küçük sıralama', 'basari siralamasi', 'siralamasi', 'sıralaması', 'başarı sırası / sıralaması']
    }
    
    tum_df_listesi = []

    for dosya in excel_dosyalari:
        dosya_tam_yolu = os.path.join(klasor_yolu, dosya)
        print(f"\n📖 {dosya} okunuyor ve akıllı sütun hizalaması yapılıyor...")
        try:
            df = pd.read_excel(dosya_tam_yolu)
            
            # Kolon başlıklarının sağındaki solundaki boşlukları temizleyelim
            df.columns = [str(c).strip() for c in df.columns]
            
            hizalanmis_df = pd.DataFrame(columns=standart_sutunlar)
            
            for std_col, varyasyonlar in eslesme_sozlugu.items():
                eslesen_kolon_adi = None
                for col in df.columns:
                    if col.lower() in [v.lower() for v in varyasyonlar]:
                        eslesen_kolon_adi = col
                        break
                
                if eslesen_kolon_adi is not None:
                    hizalanmis_df[std_col] = df[eslesen_kolon_adi]
                    print(f"   ✔️  '{eslesen_kolon_adi}' kolonu başarıyla '{std_col}' olarak eşleştirildi.")
                else:
                    hizalanmis_df[std_col] = "-"
                    
            tum_df_listesi.append(hizalanmis_df)
        except Exception as e:
            print(f"⚠️  {dosya} işlenirken bir hata oluştu: {e}")

    if not tum_df_listesi:
        print("❌ HATA: Aktarılacak geçerli bir veri bulunamadı!")
        return

    # Tüm tabloları tek bir standartta birleştiriyoruz
    print("\n🔄 Tüm tablolar tek bir standartta birleştiriliyor...")
    birlesmis_df = pd.concat(tum_df_listesi, ignore_index=True)

    # Veritabanı bağlantısı
    conn = sqlite3.connect(db_yolu)
    
    print("💾 Birleşmiş ve sıralanmış veriler 'veritabani.db' dosyasına yazılıyor...")
    birlesmis_df.to_sql('yks_taban_puanlari', conn, if_exists='replace', index=False)
    
    conn.close()
    print(f"🎉 TEBRİKLER! Toplam {len(birlesmis_df)} satır veri başarıyla aktarıldı.")

if __name__ == "__main__":
    tum_verileri_tabana_aktar()
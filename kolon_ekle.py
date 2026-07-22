import sqlite3

conn = sqlite3.connect('veritabani.db')
cursor = conn.cursor()

try:
    # Tabloya onayli kolonunu varsayılan olarak 0 (onaysız) olacak şekilde ekliyoruz
    cursor.execute("ALTER TABLE ataturk_notlari ADD COLUMN onayli INTEGER DEFAULT 0")
    conn.commit()
    print("Kolon başarıyla eklendi! Artık admin paneli çalışacaktır.")
except sqlite3.OperationalError:
    print("Kolon zaten mevcut veya bir hata oluştu.")

conn.close()
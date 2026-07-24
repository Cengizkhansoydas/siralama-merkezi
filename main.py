from flask import Flask, render_template, request, jsonify, send_from_directory, abort
import sqlite3
import math
import csv
import os

app = Flask(__name__)

# --- ADS.TXT ROTASI (Buraya ekliyoruz) ---
@app.route('/ads.txt')
def ads_txt():
    return send_from_directory(app.root_path, 'ads.txt')


# ==============================================================================
# 🛠️ YARDIMCI VERİTABANI VE DOSYA FONKSİYONLARI (En Tepede Olmalı)
# ==============================================================================

def csv_oku(dosya_adi):
    # CSV dosyaların 'data' klasöründe olmalı
    yol = os.path.join('data', f"{dosya_adi}.csv")
    if not os.path.exists(yol): return [], []
    with open(yol, encoding='utf-8') as f:
        reader = list(csv.reader(f))
        return reader[0], reader[1:]

def db_query(query, params=()):
    conn = sqlite3.connect('veritabani.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result

def get_valid_column_name(table_name, target_names):
    """Veritabanındaki kolon isimlerini güvenli bir şekilde kontrol eder"""
    try:
        conn = sqlite3.connect('veritabani.db')
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1].lower() for col in cursor.fetchall()]
        conn.close()
        for name in target_names:
            if name.lower() in columns: return [c for c in columns if c == name.lower()][0]
    except Exception as e:
        print("Kolon ismi kontrol edilirken hata:", e)
    return target_names[0]

# =====================================================================
# 🧮 Geliştirilmiş ÖSYM Katsayı ve Gerçekçi Yığılma Motoru
# =====================================================================
class VePuanEngine:
    TABAN_PUAN = 100.0
    KATSAYILAR = {
        2025: {"TYT": {"tur": 1.33, "mat": 1.33, "sos": 1.37, "fen": 1.37}, "SAY": {"mat": 3.05, "fiz": 2.88, "kim": 3.02, "biyo": 3.12}, "EA": {"mat": 3.05, "ede": 2.98, "tar1": 2.82, "cog1": 3.22}, "SOZ": {"ede": 2.98, "tar1": 2.82, "cog1": 3.22, "tar2": 2.92, "cog2": 2.92, "fel": 3.02, "din": 3.32}, "dil": 3.00},
        2024: {"TYT": {"tur": 1.32, "mat": 1.32, "sos": 1.36, "fen": 1.36}, "SAY": {"mat": 3.00, "fiz": 2.85, "kim": 3.05, "biyo": 3.10}, "EA": {"mat": 3.00, "ede": 3.00, "tar1": 2.80, "cog1": 3.20}, "SOZ": {"ede": 3.00, "tar1": 2.80, "cog1": 3.20, "tar2": 2.90, "cog2": 2.90, "fel": 3.00, "din": 3.30}, "dil": 2.90},
        2023: {"TYT": {"tur": 1.33, "mat": 1.33, "sos": 1.38, "fen": 1.38}, "SAY": {"mat": 3.10, "fiz": 2.90, "kim": 3.00, "biyo": 3.15}, "EA": {"mat": 3.10, "ede": 2.95, "tar1": 2.85, "cog1": 3.25}, "SOZ": {"ede": 2.95, "tar1": 2.85, "cog1": 3.25, "tar2": 2.95, "cog2": 2.95, "fel": 3.05, "din": 3.35}, "dil": 2.80},
        2022: {"TYT": {"tur": 1.32, "mat": 1.32, "sos": 1.37, "fen": 1.37}, "SAY": {"mat": 3.02, "fiz": 2.87, "kim": 3.01, "biyo": 3.11}, "EA": {"mat": 3.02, "ede": 2.99, "tar1": 2.81, "cog1": 3.21}, "SOZ": {"ede": 2.99, "tar1": 2.81, "cog1": 3.21, "tar2": 2.91, "cog2": 2.91, "fel": 3.01, "din": 3.31}, "dil": 2.90}
    }

    @staticmethod
    def tyt_ham_hesapla(netler, yil):
        k = VePuanEngine.KATSAYILAR[yil]["TYT"]
        puan = VePuanEngine.TABAN_PUAN
        puan += netler.get("tyt_tr", 0) * k["tur"]
        puan += netler.get("tyt_mat", 0) * k["mat"]
        puan += netler.get("tyt_sos", 0) * k["sos"]
        puan += netler.get("tyt_fen", 0) * k["fen"]
        return round(min(500.0, max(100.0, puan)), 3)

    @staticmethod
    def say_ham_hesapla(tyt_ham, netler, yil):
        k = VePuanEngine.KATSAYILAR[yil]["SAY"]
        tyt_katki = (tyt_ham - 100.0) * 0.4
        ayt_puan = 100.0 + tyt_katki
        ayt_puan += netler.get("ayt_mat", 0) * k["mat"]
        ayt_puan += netler.get("ayt_fiz", 0) * k["fiz"]
        ayt_puan += netler.get("ayt_kim", 0) * k["kim"]
        ayt_puan += netler.get("ayt_biyo", 0) * k["biyo"]
        return round(min(500.0, max(100.0, ayt_puan)), 3)

    @staticmethod
    def ea_ham_hesapla(tyt_ham, netler, yil):
        k = VePuanEngine.KATSAYILAR[yil]["EA"]
        tyt_katki = (tyt_ham - 100.0) * 0.4
        ayt_puan = 100.0 + tyt_katki
        ayt_puan += netler.get("ayt_mat", 0) * k["mat"]
        ayt_puan += netler.get("ayt_ede", 0) * k["ede"]
        ayt_puan += netler.get("ayt_tar1", 0) * k["tar1"]
        ayt_puan += netler.get("ayt_cog1", 0) * k["cog1"]
        return round(min(500.0, max(100.0, ayt_puan)), 3)

    @staticmethod
    def soz_ham_hesapla(tyt_ham, netler, yil):
        k = VePuanEngine.KATSAYILAR[yil]["SOZ"]
        tyt_katki = (tyt_ham - 100.0) * 0.4
        ayt_puan = 100.0 + tyt_katki
        ayt_puan += netler.get("ayt_ede", 0) * k["ede"]
        ayt_puan += netler.get("ayt_tar1", 0) * k["tar1"]
        ayt_puan += netler.get("ayt_cog1", 0) * k["cog1"]
        ayt_puan += netler.get("ayt_tar2", 0) * k["tar2"]
        ayt_puan += netler.get("ayt_cog2", 0) * k["cog2"]
        ayt_puan += netler.get("ayt_fel", 0) * k["fel"]
        ayt_puan += netler.get("ayt_din", 0) * k["din"]
        return round(min(500.0, max(100.0, ayt_puan)), 3)

    @staticmethod
    def dil_ham_hesapla(tyt_ham, netler, yil):
        v = VePuanEngine.KATSAYILAR[yil]
        tyt_katki = (tyt_ham - 100.0) * 0.4
        ayt_puan = 100.0 + tyt_katki
        ayt_puan += netler.get("dil_test", 0) * v["dil"]
        return round(min(500.0, max(100.0, ayt_puan)), 3)

    @staticmethod
    def siralama_tahmin_et(puan, puan_turu, yil):
        if puan <= 100.5: return "---"
        diff = 500.0 - puan
        if diff <= 0: return "1"
        tur_ayarlari = {"TYT": {"taban_carpan": 0.045, "ust": 2.41}, "SAY": {"taban_carpan": 0.009, "ust": 2.58}, "EA": {"taban_carpan": 0.022, "ust": 2.48}, "SÖZ": {"taban_carpan": 0.120, "ust": 2.30}, "DİL": {"taban_carpan": 0.015, "ust": 2.42}}
        ayar = tur_ayarlari.get(puan_turu, {"taban_carpan": 0.03, "ust": 2.4})
        yil_carpanlari = {2025: {"TYT": 1.00, "SAY": 1.00, "EA": 1.00, "SÖZ": 1.00, "DİL": 1.00}, 2024: {"TYT": 1.12, "SAY": 0.78, "EA": 0.90, "SÖZ": 1.18, "DİL": 1.08}, 2023: {"TYT": 1.18, "SAY": 1.14, "EA": 1.10, "SÖZ": 1.25, "DİL": 1.12}, 2022: {"TYT": 1.05, "SAY": 0.95, "EA": 1.02, "SÖZ": 1.08, "DİL": 1.05}}
        indeks = yil_carpanlari.get(yil, {}).get(puan_turu, 1.0)
        sira = int((diff ** ayar["ust"]) * ayar["taban_carpan"] * indeks)
        return f"{max(1, sira):,}".replace(",", ".")

# =====================================================================
# 🌐 1. KATMAN: ANA SAYFA VE STATİK (SABİT) SAYFA ROTALARI
# =====================================================================

@app.route('/')
def ana_sayfa():
    populer_bolumler = [{"isim": "Tıp Fakültesi", "link": "tip", "ikon": "fa-user-md"}, {"isim": "Bilgisayar Mühendisliği", "link": "bilgisayar-muhendisligi", "ikon": "fa-laptop-code"}, {"isim": "Hukuk Fakültesi", "link": "hukuk", "ikon": "fa-gavel"}, {"isim": "Diş Hekimliği", "link": "dis-hekimligi", "ikon": "fa-tooth"}, {"isim": "Hemşirelik", "link": "hemsirelik", "ikon": "fa-user-nurse"}, {"isim": "Makine Mühendisliği", "link": "makine-muhendisligi", "ikon": "fa-cogs"}]
    return render_template('ana_sayfa.html', bolumler=populer_bolumler)

@app.route('/yks/soru-dagilimlari')
def soru_dagilimlari_paneli():
    """Çakışması çözülen, doğrudan soru_dagilimlari.html'e giden özel rota"""
    yillar, satirlar = csv_oku('ayt_matematik')
    if yillar and not yillar[0].strip().isdigit():
        yillar = yillar[1:]
    return render_template('soru_dagilimlari.html', yillar=yillar, satirlar=satirlar)

@app.route('/yks/konular')
def yks_konular_sayfasi():
    return render_template('yks_konulari.html')

@app.route('/dgs/konular')
def dgs_konulari():
    return render_template('dgs_konulari.html')

@app.route('/hesaplama/dgs')
def dgs_hesaplama():
    return render_template('dgs_hesaplama.html')
        
@app.route('/lgs/konular')
def lgs_konulari_sayfasi():
    return render_template('lgs_konulari.html')

@app.route('/hesaplama/lgs')
def lgs_hesaplama():
    return render_template('lgs_hesaplama.html')

@app.route('/ales/konular')
def ales_konulari():
    return render_template('ales_konulari.html')

@app.route('/msu/konular')
def msu_konulari():
    return render_template('msu_konulari.html')

@app.route('/yds/konular')
def yds_konulari():
    return render_template('yds_konulari.html')

@app.route('/kpss/konular')
def kpss_konulari():
    return render_template('kpss_konulari.html')

@app.route('/hesaplama/obp')
@app.route('/obp-hesaplama')
def obp_hesaplama():
    return render_template('obp_hesaplama.html')
               
@app.route('/yks/ayt-matematik')
def ayt_matematik():
    yillar, satirlar = csv_oku('ayt_matematik')
    if yillar and not yillar[0].strip().isdigit():
        yillar = yillar[1:]
    return render_template('ayt_matematik.html', yillar=yillar, satirlar=satirlar)

@app.route('/yks/ayt-edebiyat')
def ayt_edebiyat():
    try:
        # Veritabanından verileri çekiyoruz
        tum_veri = db_query("SELECT * FROM yks_konu_ayt_edebiyat")
        
        if not tum_veri:
            return render_template('ayt_edebiyat.html', yillar=[], satirlar=[], hata="Veritabanında veri yok, önce aktar.py çalıştır.")
            
        # Yılları (kolon isimlerini) dinamik alıyoruz
        conn = sqlite3.connect('veritabani.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(yks_konu_ayt_edebiyat)")
        kolonlar = [col[1] for col in cursor.fetchall()]
        conn.close()
        
        yillar = kolonlar[1:] # İlk sütun konu adı, gerisi yıllar
        satirlar = [list(satir) for satir in tum_veri]
        
        return render_template('ayt_edebiyat.html', yillar=yillar, satirlar=satirlar)
    except Exception as e:
        return render_template('ayt_edebiyat.html', yillar=[], satirlar=[], hata=str(e))    

@app.route('/ataturk-kosesi')
def ataturk_kosesi():
    """Atatürk Köşesi: Sadece onaylanan notları getirir"""
    try:
        # WHERE onayli = 1 ekledik!
        notlar = db_query("SELECT isim, not_metni, tarih FROM ataturk_notlari WHERE onayli = 1 ORDER BY id DESC")
    except:
        notlar = [] # Hata olursa boş dönsün
    return render_template('ataturk_kosesi.html', notlar=notlar)

@app.route('/ataturk-kosesi/not-bira', methods=['POST'])
def not_birak():
    """Öğrencilerin notunu onaysız (0) olarak kaydeder"""
    isim = request.form.get('isim', 'Gizli Üye')
    not_metni = request.form.get('not_metni', '')
    import datetime
    bugun = datetime.datetime.now().strftime("%d.%m.%Y")
    
    if not_metni:
        try:
            conn = sqlite3.connect('veritabani.db')
            cursor = conn.cursor()
            
            # 🔥 GEÇİCİ AŞI: Eğer tabloda 'onayli' sütunu yoksa kod hata vermeden burası ekleyecek!
            try:
                cursor.execute("ALTER TABLE ataturk_notlari ADD COLUMN onayli INTEGER DEFAULT 0;")
                conn.commit()
            except:
                # Sütun zaten varsa veya eklendiyse burası sessizce geçecek, hata vermeyecek
                pass

            cursor.execute("INSERT INTO ataturk_notlari (isim, not_metni, tarih, onayli) VALUES (?, ?, ?, 0)", (isim, not_metni, bugun))
            conn.commit()
            conn.close()
        except Exception as e:
            print("Not veritabanına kaydedilemedi:", e)
            
    return jsonify({"durum": "success"})
# =====================================================================
# 📝 2. KATMAN: DİNAMİK DERS VE MÜFREDAT ROTALARI (BİREBİR EŞLEŞTİRİLDİ)
# =====================================================================

@app.route('/yks/konular/<ders_kodu>')
def dinamik_ders_sayfalari(ders_kodu):
    # Sol taraftaki templates/ klasöründe yer alan dosya isimlerinle eşleme yapıyoruz
    if ders_kodu in ['ayt-tarih-1', 'ayt-tarih-2']:
        tablo_adi = 'yks_konu_ayt_tarih'
        sablon_adi = 'ayt_tarih'
    elif ders_kodu == 'tyt-din-kulturu':
        tablo_adi = 'yks_konu_tyt_din'
        sablon_adi = 'tyt_din'  # templates/tyt_din.html dosyasını çağırır
    elif ders_kodu == 'ayt-din-kulturu':
        tablo_adi = 'yks_konu_ayt_din'
        sablon_adi = 'ayt_din'  # templates/ayt_din.html dosyasını çağırır
    else:
        tablo_adi = f"yks_konu_{ders_kodu.replace('-', '_')}"
        sablon_adi = ders_kodu.replace('-', '_')
        
    try:
        tum_veri = db_query(f"SELECT * FROM {tablo_adi}")
        
        yillar = []
        satirlar = []
        
        if tum_veri:
            conn = sqlite3.connect('veritabani.db')
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({tablo_adi})")
            kolonlar = [col[1] for col in cursor.fetchall()]
            conn.close()
            
            yillar = kolonlar[1:]
            satirlar = [list(satir) for satir in tum_veri]
            
        return render_template(f"{sablon_adi}.html", 
                               yillar=yillar, 
                               satirlar=satirlar, 
                               ders_adi=ders_kodu.replace('-', ' ').upper())
    except Exception as e:
        print(f"Veritabanından {tablo_adi} tablosu okunurken hata:", e)
        abort(404)
# =====================================================================
# 🔍 3. KATMAN: SORGULAMA VE HESAPLAMA MOTORU ROTALARI
# =====================================================================

@app.route('/ara')
def ara():
    klavye_girdisi = request.args.get('q', '')
    meslek_link = request.args.get('meslek', '')
    
    # URL'den gelen meslek linkini veritabanı kelimesine eşleme
    meslek_filtresi = "Tıp" if meslek_link == "tip" else "Bilgisayar Mühendisliği" if meslek_link == "bilgisayar-muhendisligi" else "Hukuk" if meslek_link == "hukuk" else meslek_link.replace("-", " ")
    
    col_bolum = get_valid_column_name('yks_taban_puanlari', ['bölüm', 'bolum', 'program', 'program_adi'])
    col_uni = get_valid_column_name('yks_taban_puanlari', ['üniversite', 'universite', 'uni', 'universite_adi'])
    
    # Arama motorunda sadece aktif olunan meslek grubunun içinde filtreleme yapar
    if klavye_girdisi:
        sorgu = f"SELECT * FROM yks_taban_puanlari WHERE {col_bolum} LIKE ? AND ({col_uni} LIKE ? OR {col_uni} LIKE ? OR {col_bolum} LIKE ?)"
        parametreler = ('%' + meslek_filtresi + '%', '%' + klavye_girdisi + '%', '%' + klavye_girdisi.upper() + '%', '%' + klavye_girdisi + '%')
    else:
        sorgu = f"SELECT * FROM yks_taban_puanlari WHERE {col_bolum} LIKE ?"
        parametreler = ('%' + meslek_filtresi + '%',)
        
    veriler = db_query(sorgu, parametreler)
    return jsonify(veriler)

@app.route('/hesaplama/yks', methods=['GET', 'POST'])
def yks_hesaplama():
    if request.method == 'POST':
        try:
            diploma_notu = float(request.form.get('diploma_notu', 90) or 90)
            kirik_obp = request.form.get('onceki_yerlesme') == 'on'
            obp_katki = diploma_notu * 5.0 * (0.06 if kirik_obp else 0.12)
            def get_net_from_inputs(name):
                d = float(request.form.get(f'{name}_d', 0) or 0)
                y = float(request.form.get(f'{name}_y', 0) or 0)
                return max(0.0, d - (y * 0.25))
            netler = {"tyt_tr": get_net_from_inputs('tyt_tr'), "tyt_sos": get_net_from_inputs('tyt_sos'), "tyt_mat": get_net_from_inputs('tyt_mat'), "tyt_fen": get_net_from_inputs('tyt_fen'), "ayt_mat": get_net_from_inputs('ayt_mat'), "ayt_fiz": get_net_from_inputs('ayt_fiz'), "ayt_kim": get_net_from_inputs('ayt_kim'), "ayt_biyo": get_net_from_inputs('ayt_biyo'), "ayt_ede": get_net_from_inputs('ayt_ede'), "ayt_tar1": get_net_from_inputs('ayt_tar1'), "ayt_cog1": get_net_from_inputs('ayt_cog1'), "ayt_tar2": get_net_from_inputs('ayt_tar2'), "ayt_cog2": get_net_from_inputs('ayt_cog2'), "ayt_fel": get_net_from_inputs('ayt_fel'), "ayt_din": get_net_from_inputs('ayt_din'), "dil_test": get_net_from_inputs('dil_test')}
            yillar = [2025, 2024, 2023, 2022]
            puan_kartlari = {}
            for y in yillar:
                tyt_ham = VePuanEngine.tyt_ham_hesapla(netler, yil=y)
                say_ham = VePuanEngine.say_ham_hesapla(tyt_ham, netler, yil=y)
                ea_ham = VePuanEngine.ea_ham_hesapla(tyt_ham, netler, yil=y)
                soz_ham = VePuanEngine.soz_ham_hesapla(tyt_ham, netler, yil=y)
                dil_ham = VePuanEngine.dil_ham_hesapla(tyt_ham, netler, yil=y)
                puan_kartlari[str(y)] = [{"tur": "TYT", "ham": tyt_ham, "ham_sir": VePuanEngine.siralama_tahmin_et(tyt_ham, "TYT", y), "yer": round(tyt_ham + obp_katki, 3), "yer_sir": VePuanEngine.siralama_tahmin_et(tyt_ham + obp_katki, "TYT", y)}, {"tur": "SÖZ", "ham": soz_ham, "ham_sir": VePuanEngine.siralama_tahmin_et(soz_ham, "SÖZ", y), "yer": round(soz_ham + obp_katki, 3), "yer_sir": VePuanEngine.siralama_tahmin_et(soz_ham + obp_katki, "SÖZ", y)}, {"tur": "EA", "ham": ea_ham, "ham_sir": VePuanEngine.siralama_tahmin_et(ea_ham, "EA", y), "yer": round(ea_ham + obp_katki, 3), "yer_sir": VePuanEngine.siralama_tahmin_et(ea_ham + obp_katki, "EA", y)}, {"tur": "SAY", "ham": say_ham, "ham_sir": VePuanEngine.siralama_tahmin_et(say_ham, "SAY", y), "yer": round(say_ham + obp_katki, 3), "yer_sir": VePuanEngine.siralama_tahmin_et(say_ham + obp_katki, "SAY", y)}, {"tur": "DİL", "ham": dil_ham, "ham_sir": VePuanEngine.siralama_tahmin_et(dil_ham, "DİL", y), "yer": round(dil_ham + obp_katki, 3), "yer_sir": VePuanEngine.siralama_tahmin_et(dil_ham + obp_katki, "DİL", y)}]
            sonuclar = {"hesaplandi": True, "puan_kartlari": puan_kartlari}
            return render_template('yks_hesaplama.html', sonuclar=sonuclar)
        except Exception as e:
            return render_template('yks_hesaplama.html', sonuclar={"hesaplandi": False}, hata=str(e))
    return render_template('yks_hesaplama.html', sonuclar={"hesaplandi": False})

# =====================================================================
# 🎓 4. KATMAN: EN ALTA BIRAKILAN DİNAMİK MESLEK/TABAN PUAN ROTASI
# =====================================================================

@app.route('/yks-siralamalari')
def yks_siralamalari_secim_ekrani():
    """Bütün bölümlerin listelendiği ana kartlı yönlendirme sayfası (Seçim Ekranı)"""
    return render_template('bolumler.html')

@app.route('/yks/<meslek_link>')
def meslek_sayfasi(meslek_link):
    """
    Tüm Türkçe karakter sorunlarını çözen, sözlük tabanlı nokta atışı rota.
    """
    # 🎯 BURASI ALTIN ANAHTAR: 
    # Sol tarafa linkteki hali (küçük harfli, tiresiz), 
    # Sağ tarafa ise Excel'inde ve bolumler.html'de yazan birebir TÜRKÇE adını yazıyoruz.
    sozluk = {
        "acil-yardim-ve-afet-yonetimi": "Acil Yardım ve Afet Yönetimi",
        "adli-bilimler": "Adli Bilimler",
        "adli-bilisim-muhendisligi": "Adli Bilişim Mühendisliği",
        "agac-isleri-endustri-muhendisligi": "Ağaç İşleri Endüstri Mühendisliği",
        "aile-ve-tuketici-bilimleri": "Aile ve Tüketici Bilimleri",
        "aktuerya-bilimleri": "Aktüerya Bilimleri",
        "alman-dili-ve-edebiyati": "Alman Dili ve Edebiyatı",
        "almanca-mutercim-ve-tercumanlik": "Almanca Mütercim ve Tercümanlık",
        "almanca-ogretmenligi": "Almanca Öğretmenliği",
        "amerikan-kulturu-ve-edebiyati": "Amerikan Kültürü ve Edebiyatı",
        "antrenorluk-egitimi": "Antrenörlük Eğitimi",
        "antropoloji": "Antropoloji",
        "arap-dili-ve-edebiyati": "Arap Dili ve Edebiyatı",
        "arapca-mutercim-ve-tercumanlik": "Arapça Mütercim ve Tercümanlık",
        "arapca-ogretmenligi": "Arapça Öğretmenliği",
        "arkeoloji": "Arkeoloji",
        "arkeoloji-ve-sanat-tarihi": "Arkeoloji ve Sanat Tarihi",
        "arnavut-dili-ve-edebiyati": "Arnavut Dili ve Edebiyatı",
        "astronomi-ve-uzay-bilimleri": "Astronomi ve Uzay Bilimleri",
        "ayakkabi-tasarimi-ve-uretimi": "Ayakkabı Tasarımı ve Üretimi",
        "azerbaycan-turkcesi-ve-edebiyati": "Azerbaycan Türkçesi ve Edebiyatı",
        "bahce-bitkileri": "Bahçe Bitkileri",
        "balikcilik-teknolojisi-muhendisligi": "Balıkçılık Teknolojisi Mühendisliği",
        "bankacilik": "Bankacılık",
        "bankacilik-ve-finans": "Bankacılık ve Finans",
        "bankacilik-ve-sigortacilik": "Bankacılık ve Sigortacılık",
        "basim-teknolojileri": "Basım Teknolojileri",
        "basin-ve-yayin": "Basın ve Yayın",
        "bati-dilleri": "Batı Dilleri",
        "beden-egitimi-ve-spor-ogretmenligi": "Beden Eğitimi ve Spor Öğretmenliği",
        "beslenme-ve-diyetetik": "Beslenme ve Diyetetik",
        "bilgi-guvenligi-teknolojisi": "Bilgi Güvenliği Teknolojisi",
        "bilgi-ve-belge-yonetimi": "Bilgi ve Belge Yönetimi",
        "bilgisayar-bilimleri": "Bilgisayar Bilimleri",
        "bilgisayar-muhendisligi": "Bilgisayar Mühendisliği",
        "bilgisayar-teknolojisi-ve-bilisim-sistemleri": "Bilgisayar Teknolojisi ve Bilişim Sistemleri",
        "bilgisayar-ve-ogretim-teknolojileri-ogretmenligi": "Bilgisayar ve Öğretim Teknolojileri Öğretmenliği",
        "bilim-tarihi": "Bilim Tarihi",
        "bilisim-sistemleri-muhendisligi": "Bilişim Sistemleri Mühendisliği",
        "bilisim-sistemleri-ve-teknolojileri": "Bilişim Sistemleri ve Teknolojileri",
        "bitki-koruma": "Bitki Koruma",
        "bitkisel-uretim-ve-teknolojileri": "Bitkisel Üretim ve Teknolojileri",
        "biyokimya": "Biyokimya",
        "biyoloji-ogretmenligi": "Biyoloji Öğretmenliği",
        "biyoloji": "Biyoloji",
        "biyomedikal-muhendisligi": "Biyomedikal Mühendisliği",
        "biyomuehendislik": "Biyomühendislik",
        "biyosistem-muhendisligi": "Biyosistem Mühendisliği",
        "biyoteknoloji": "Biyoteknoloji",
        "bosnak-dili-ve-edebiyati": "Boşnak Dili ve Edebiyatı",
        "bulgar-dili-ve-edebiyati": "Bulgar Dili ve Edebiyatı",
        "bulgarca-mutercim-ve-tercumanlik": "Bulgarca Mütercim ve Tercümanlık",
        "cevher-hazirlama-muhendisligi": "Cevher Hazırlama Mühendisliği",
        "cografya-ogretmenligi": "Coğrafya Öğretmenliği",
        "cografya": "Coğrafya",
        "cagdas-turk-lehceleri-ve-edebiyatlari": "Çağdaş Türk Lehçeleri ve Edebiyatları",
        "cagdas-yunan-dili-ve-edebiyati": "Çağdaş Yunan Dili ve Edebiyatı",
        "calisma-ekonomisi-ve-endustri-iliskileri": "Çalışma Ekonomisi ve Endüstri İlişkileri",
        "cerkez-dili-ve-edebiyati": "Çerkez Dili ve Edebiyatı",
        "ceviribilim": "Çeviribilim",
        "cevre-muhendisligi": "Çevre Mühendisliği",
        "cin-dili-ve-edebiyati": "Çin Dili ve Edebiyatı",
        "cince-mutercim-ve-tercumanlik": "Çince Mütercim ve Tercümanlık",
        "cizgi-film-ve-animasyon": "Çizgi Film ve Animasyon",
        "cocuk-gelisimi": "Çocuk Gelişimi",
        "deniz-ulastirma-isletme-muhendisligi": "Deniz Ulaştırma İşletme Mühendisliği",
        "denizcilik-isletmeleri-yonetimi": "Denizcilik İşletmeleri Yönetimi",
        "deri-muhendisligi": "Deri Mühendisliği",
        "dijital-oyun-tasarimi": "Dijital Oyun Tasarımı",
        "dil-ve-konusma-terapisi": "Dil ve Konuşma Terapisi",
        "dilbilimi": "Dilbilimi",
        "dis-hekimligi": "Diş Hekimliği",
        "dogu-dilleri": "Doğu Dilleri",
        "ebelik": "Ebelik",
        "eczacilik": "Eczacılık",
        "egzersiz-ve-spor-bilimleri": "Egzersiz ve Spor Bilimleri",
        "ekonometri": "Ekonometri",
        "ekonomi": "Ekonomi",
        "ekonomi-ve-finans": "Ekonomi ve Finans",
        "el-sanatlari": "El Sanatları",
        "elektrik-muhendisligi": "Elektrik Mühendisliği",
        "elektrik-elektronik-muhendisligi": "Elektrik-Elektronik Mühendisliği",
        "elektronik-muhendisligi": "Elektronik Mühendisliği",
        "elektronik-ticaret-ve-yonetimi": "Elektronik Ticaret Ve Yönetimi",
        "elektronik-ve-haberlesme-muhendisligi": "Elektronik ve Haberleşme Mühendisliği",
        "emlak-ve-emlak-yonetimi": "Emlak Ve Emlak Yönetimi",
        "endustri-muhendisligi": "Endüstri Mühendisliği",
        "endustriyel-tasarim-muhendisligi": "Endüstriyel Tasarım Mühendisliği",
        "endustriyel-tasarim": "Endüstriyel Tasarım",
        "enerji-bilimi-ve-teknolojileri": "Enerji Bilimi ve Teknolojileri",
        "enerji-sistemleri-muhendisligi": "Enerji Sistemleri Mühendisliği",
        "enerji-yonetimi": "Enerji Yönetimi",
        "ergoterapi": "Ergoterapi",
        "ermeni-dili-ve-kulturu": "Ermeni Dili ve Kültürü",
        "eski-yunan-dili-ve-edebiyati": "Eski Yunan Dili ve Edebiyatı",
        "fars-dili-ve-edebiyati": "Fars Dili ve Edebiyatı",
        "farsca-mutercim-ve-tercumanlik": "Farsça Mütercim ve Tercümanlık",
        "felsefe-grubu-ogretmenligi": "Felsefe Grubu Öğretmenliği",
        "felsefe": "Felsefe",
        "fen-bilgisi-ogretmenligi": "Fen Bilgisi Öğretmenliği",
        "film-tasarim-ve-yonetmenligi": "Film Tasarım ve Yönetmenliği",
        "film-tasarimi-ve-yazarligi": "Film Tasarımı ve Yazarlığı",
        "film-tasarimi-ve-yonetimi": "Film Tasarımı ve Yönetimi",
        "finans-ve-bankacilik": "Finans ve Bankacılık",
        "fizik-muhendisligi": "Fizik Mühendisliği",
        "fizik-ogretmenligi": "Fizik Öğretmenliği",
        "fizik": "Fizik",
        "fizyoterapi-ve-rehabilitasyon": "Fizyoterapi ve Rehabilitasyon",
        "fotograf": "Fotoğraf",
        "fotograf-ve-video": "Fotoğraf ve Video",
        "fotonik": "Fotonik",
        "fransiz-dili-ve-edebiyati": "Fransız Dili ve Edebiyatı",
        "fransizca-mutercim-ve-tercumanlik": "Fransızca Mütercim ve Tercümanlık",
        "fransizca-ogretmenligi": "Fransızca Öğretmenliği",
        "gastronomi-ve-mutfak-sanatlari": "Gastronomi ve Mutfak Sanatları",
        "gayrimenkul-gelistirme-ve-yonetimi": "Gayrimenkul Geliştirme ve Yönetimi",
        "gazetecilik": "Gazetecilik",
        "geleneksel-turk-sanatlari": "Geleneksel Türk Sanatları",
        "gemi-insaat-ve-gemi-makineleri-muhendisligi": "Gemi İnşaatı ve Gemi Makineleri Mühendisliği",
        "gemi-makineleri-isletme-muhendisligi": "Gemi Makineleri İşletme Mühendisliği",
        "gemi-ve-deniz-teknolojisi-muhendisligi": "Gemi ve Deniz Teknolojisi Mühendisliği",
        "gemi-ve-yat-tasarimi": "Gemi ve Yat Tasarımı",
        "genetik-ve-biyomuhendislik": "Genetik ve Biyomühendislik",
        "genetik-ve-yasam-bilimleri-programlari": "Genetik ve Yaşam Bilimleri Programları",
        "geomatik-muhendisligi": "Geomatik Mühendisliği",
        "gerontoloji": "Gerontoloji",
        "gida-muhendisligi": "Gıda Mühendisliği",
        "gida-teknolojisi": "Gıda Teknolojisi",
        "girisimcilik": "Girişimcilik",
        "gorsel-iletisim-tasarimi": "Görsel İletişim Tasarımı",
        "gorsel-sanatlar": "Görsel Sanatlar",
        "gorsel-sanatlar-ve-iletisim": "Görsel Sanatlar ve İletişim",
        "grafik-sanatlar": "Grafik Sanatlar",
        "grafik": "Grafik",
        "grafik-tasarimi": "Grafik Tasarımı",
        "gumruk-isletme": "Gümrük İşletme",
        "gurcu-dili-ve-edebiyati": "Gürcü Dili ve Edebiyatı",
        "halkbilim": "Halkbilim",
        "halkla-iliskiler-ve-reklamcilik": "Halkla İlişkiler ve Reklamcılık",
        "halkla-iliskiler-ve-tanitim": "Halkla İlişkiler ve Tanıtım",
        "harita-muhendisligi": "Harita Mühendisliği",
        "havacilik-elektrik-ve-elektronigi": "Havacılık Elektrik ve Elektroniği",
        "havacilik-ve-uzay-muhendisligi": "Havacılık ve Uzay Mühendisliği",
        "havacilik-yonetimi": "Havacılık Yönetimi",
        "hayvansal-uretim-ve-teknolojileri": "Hayvansal Üretim ve Teknolojileri",
        "hemsirelik": "Hemşirelik",
        "hidrojeoloji-muhendisligi": "Hidrojeoloji Mühendisliği",
        "hindoloji": "Hindoloji",
        "hititoloji": "Hititoloji",
        "hukuk": "Hukuk",
        "hungaroloji": "Hungaroloji",
        "ibrani-dili-ve-kulturu": "İbrani Dili ve Kültürü",
        "ic-mimarlik": "İç Mimarlık",
        "ic-mimarlik-ve-cevre-tasarimi": "İç Mimarlık ve Çevre Tasarımı",
        "iktisadi-ve-idari-bilimler-programlari": "İktisadi ve İdari Bilimler Programları",
        "iktisat": "İktisat",
        "ilahiyat": "İlahiyat",
        "iletisim-bilimleri": "İletişim Bilimleri",
        "iletisim-fakultesi": "İletişim Fakültesi",
        "iletisim-sanatlari": "İletişim Sanatları",
        "iletisim-tasarimi-ve-yonetimi": "İletişim Tasarımı ve Yönetimi",
        "iletisim-ve-tasarim": "İletişim ve Tasarım",
        "ilkogretim-matematik-ogretmenligi": "İlköğretim Matematik Öğretmenliği",
        "imalat-muhendisligi": "İmalat Mühendisliği",
        "ingiliz-dil-bilimi": "İngiliz Dil Bilimi",
        "ingiliz-dili-ve-edebiyati": "İngiliz Dili ve Edebiyatı",
        "ingiliz-ve-rus-dilleri-ve-edebiyatlari": "İngiliz ve Rus Dilleri ve Edebiyatları",
        "ingilizce-mutercim-ve-tercumanlik": "İngilizce Mütercim ve Tercümanlık",
        "ingilizce-ogretmenligi": "İngilizce Öğretmenliği",
        "ingilizce-fransizca-mutercim-ve-tercumanlik": "İngilizce, Fransızca Mütercim ve Tercümanlık",
        "insan-kaynaklari-yonetimi": "İnsan Kaynakları Yönetimi",
        "insaat-muhendisligi": "Inşaat Mühendisliği",
        "islam-bilimleri": "İslam Bilimleri",
        "islam-iktisadi-ve-finans": "İslam İktisadı ve Finans",
        "islami-ilimler": "İslami İlimler",
        "ispanyol-dili-ve-edebiyati": "İspanyol Dili ve Edebiyatı",
        "istatistik": "İstatistik",
        "istatistik-ve-bilgisayar-bilimleri": "İstatistik ve Bilgisayar Bilimleri",
        "is-sagligi-ve-guvenligi": "İş Sağlığı ve Güvenliği",
        "isletme-muhendisligi": "İşletme Mühendisliği",
        "isletme": "İşletme",
        "italyan-dili-ve-edebiyati": "İtalyan Dili ve Edebiyatı",
        "japon-dili-ve-edebiyati": "Japon Dili ve Edebiyatı",
        "japonca-mutercim-ve-tercumanlik": "Japonca Mütercim ve Tercümanlık",
        "japonca-ogretmenligi": "Japonca Öğretmenliği",
        "jeofizik-muhendisligi": "Jeofizik Mühendisliği",
        "jeoloji-muhendisligi": "Jeoloji Mühendisliği",
        "kamu-yonetimi": "Kamu Yönetimi",
        "kanatli-hayvan-yeticiligi": "Kanatlı Hayvan Yetiştiriciliği",
        "karsilastirmali-edebiyat": "Karşılaştırmalı Edebiyat",
        "kazak-dili-ve-edebiyati": "Kazak Dili ve Edebiyatı",
        "kentsel-tasarim-ve-peyzaj-mimarligi": "Kentsel Tasarım ve Peyzaj Mimarlığı",
        "kimya-muhendisligi": "Kimya Mühendisliği",
        "kimya-ogretmenligi": "Kimya Öğretmenliği",
        "kimya": "Kimya",
        "kimya-biyoloji-muhendisligi": "Kimya-Biyoloji Mühendisliği",
        "klasik-arkeoloji": "Klasik Arkeoloji",
        "kontrol-ve-otomasyon-muhendisligi": "Kontrol ve Otomasyon Mühendisliği",
        "kore-dili-ve-edebiyati": "Kore Dili ve Edebiyatı",
        "kurgu-ses-ve-goruntu-yonetimi": "Kurgu, Ses ve Görüntü Yönetimi",
        "kuyumculuk-ve-mucevher-tasarimi": "Kuyumculuk ve Mücevher Tasarımı",
        "kultur-varliklarini-koruma-ve-onarim": "Kültür Varlıklarını Koruma ve Onarım",
        "kultur-ve-iletisim-bilimleri": "Kültür ve İletişim Bilimleri",
        "kuresel-siyaset-ve-uluslararasi-iliskiler": "Küresel Siyaset ve Uluslararası İlişkiler",
        "kurt-dili-ve-edebiyati": "Kürt Dili ve Edebiyatı",
        "latin-dili-ve-edebiyati": "Latin Dili ve Edebiyatı",
        "leh-dili-ve-edebiyati": "Leh Dili ve Edebiyatı",
        "lojistik-yonetimi": "Lojistik Yönetimi",
        "maden-muhendisligi": "Maden Mühendisliği",
        "makine-muhendisligi": "Makine Mühendisliği",
        "maliye": "Maliye",
        "malzeme-bilimi-ve-muhendisligi": "Malzeme Bilimi ve Mühendisliği",
        "malzeme-bilimi-ve-nanoteknoloji-muhendisligi": "Malzeme Bilimi ve Nanoteknoloji Mühendisliği",
        "malzeme-bilimi-ve-teknolojileri": "Malzeme Bilimi ve Teknolojileri",
        "matematik-muhendisligi": "Matematik Mühendisliği",
        "matematik-ogretmenligi": "Matematik Öğretmenliği",
        "matematik": "Matematik",
        "matematik-ve-bilgisayar-bilimleri": "Matematik ve Bilgisayar Bilimleri",
        "medya-ve-gorsel-sanatlar": "Medya ve Görsel Arts",
        "medya-ve-iletisim": "Medya ve İletişim",
        "mekatronik-muhendisligi": "Mekatronik Mühendisliği",
        "metalurji-ve-malzeme-muhendisligi": "Metalurji ve Malzeme Mühendisliği",
        "meteoroloji-muhendisligi": "Meteoroloji Mühendisliği",
        "mimarlik": "Mimarlık",
        "moda-tasarimi": "Moda Tasarımı",
        "molekuler-biyoloji-ve-genetik": "Moleküler Biyoloji ve Genetik",
        "molekuler-biyoteknoloji": "Moleküler Biyoteknoloji",
        "muhasebe-ve-finans-yonetimi": "Muhasebe ve Finans Yönetimi",
        "muhendislik-programlari": "Mühendislik Programları",
        "muhendislik-ve-doga-bilimleri-programlari": "Mühendislik ve Doğa Bilimleri Programları",
        "mutercim-tercumanlik": "Mütercim-Tercümanlık",
        "muzecilik": "Müzecilik",
        "nanobilim-ve-nanoteknoloji": "Nanobilim ve Nanoteknoloji",
        "nanoteknoloji-muhendisligi": "Nanoteknoloji Mühendisliği",
        "nukleer-enerji-muhendisligi": "Nükleer Enerji Mühendisliği",
        "odyoloji": "Odyoloji",
        "okul-oncesi-ogretmenligi": "Okul Öncesi Öğretmenliği",
        "optik-ve-akustik-muhendisligi": "Optik ve Akustik Mühendisliği",
        "organik-tarim-isletmeciligi": "Organik Tarım İşletmeciliği",
        "orman-endustri-muhendisligi": "Orman Endüstri Mühendisliği",
        "orman-muhendisligi": "Orman Mühendisliği",
        "ortez-ve-protez": "Ortez ve Protez",
        "otel-yoneticiligi": "Otel Yöneticiliği",
        "otomotiv-muhendisligi": "Otomotiv Mühendisliği",
        "ozel-egitim-ogretmenligi": "Özel Eğitim Öğretmenliği",
        "pazarlama": "Pazarlama",
        "perfuzyon": "Perfüzyon",
        "petrol-ve-dogalgaz-muhendisligi": "Petrol ve Doğalgaz Mühendisliği",
        "peyzaj-mimarligi": "Peyzaj Mimarlığı",
        "pilotaj": "Pilotaj",
        "polimer-malzeme-muhendisligi": "Polimer Malzeme Mühendisliği",
        "politika-ve-ekonomi": "Politika ve Ekonomi",
        "protohistorya-ve-on-asya-arkeolojisi": "Protohistorya ve Ön Asya Arkeolojisi",
        "psikoloji": "Psikoloji",
        "psikolojik-danismanlik-ve-rehberlik-ogretmenligi": "Psikolojik Danışmanlık ve Rehberlik Öğretmenliği",
        "radyo-televizyon-ve-sinema": "Radyo, Televizyon ve Sinema",
        "rayli-sistemler-muhendisligi": "Raylı Sistemler Mühendisliği",
        "rehberlik-ve-psikolojik-danismanlik": "Rehberlik ve Psikolojik Danışmanlık",
        "reklam-tasarimi-ve-iletisimi": "Reklam Tasarımı ve İletişimi",
        "reklamcilik": "Reklamcılık",
        "rekreasyon": "Rekreasyon",
        "rekreasyon-yonetimi": "Rekreasyon Yönetimi",
        "robotik-ve-otonom-sistemleri-muhendisligi": "Robotik ve Otonom Sistemleri Mühendisliği",
        "rus-dili-ve-edebiyati-ogretmenligi": "Rus Dili ve Edebiyatı Öğretmenliği",
        "rus-dili-ve-edebiyati": "Rus Dili ve Edebiyatı",
        "rus-ve-ingiliz-dilleri-ve-edebiyatlari": "Rus ve İngiliz Dilleri ve Edebiyatları",
        "rusca-mutercim-ve-tercumanlik": "Rusça Mütercim ve Tercümanlık",
        "saglik-yonetimi": "Sağlık Yönetimi",
        "sanat-tarihi": "Sanat Tarihi",
        "sanat-ve-kultur-yonetimi": "Sanat ve Kültür Yönetimi",
        "sanat-ve-sosyal-bilimler-programlari": "Sanat ve Sosyal Bilimler Programları",
        "sermaye-piyasasi": "Sermaye Piyasası",
        "seyahat-isletmeciligi": "Seyahat İşletmeciliği",
        "seyahat-isletmeciligi-ve-turizm-rehberligi": "Seyahat İşletmeciliği ve Turizm Rehberliği",
        "sinif-ogretmenligi": "Sınıf Öğretmenliği",
        "siber-guvenlik-muhendisligi": "Siber Güvenlik Mühendisliği",
        "sigortacilik": "Sigortacılık",
        "sigortacilik-ve-aktuerya-bilimleri": "Sigortacılık ve Aktüerya Bilimleri",
        "sigortacilik-ve-risk-yonetimi": "Sigortacılık ve Risk Yönetimi",
        "sigortacilik-ve-sosyal-guvenlik": "Sigortacılık ve Sosyal Güvenlik",
        "sinema-ve-dijital-medya": "Sinema ve Dijital Medya",
        "sinema-ve-televizyon": "Sinema ve Televizyon",
        "sinoloji": "Sinoloji",
        "siyasal-bilimler": "Siyasal Bilimler",
        "siyaset-bilimi": "Siyaset Bilimi",
        "siyaset-bilimi-ve-kamu-yonetimi": "Siyaset Bilimi ve Kamu Yönetimi",
        "siyaset-bilimi-ve-uluslararasi-iliskiler": "Siyaset Bilimi ve Uluslararası İlişkiler",
        "sosyal-bilgiler-ogretmenligi": "Sosyal Bilgiler Öğretmenliği",
        "sosyal-hizmet": "Sosyal Hizmet",
        "sosyoloji": "Sosyoloji",
        "spor-yoneticiligi": "Spor Yöneticiliği",
        "su-bilimleri-ve-muhendisligi": "Su Bilimleri ve Mühendisliği",
        "su-urunleri-muhendisligi": "Su Ürünleri Mühendisliği",
        "sumeroloji": "Sümeroloji",
        "suryani-dili-ve-edebiyati": "Süryani Dili ve Edebiyatı",
        "sut-teknolojisi": "Süt Teknolojisi",
        "sehir-ve-bolge-planlama": "Şehir ve Bölge Planlama",
        "taki-tasarimi": "Takı Tasarımı",
        "taki-tasarimi-ve-imalati": "Takı Tasarımı Ve İmalatı",
        "tapu-kadastro": "Tapu Kadastro",
        "tarim-ekonomisi": "Tarım Ekonomisi",
        "tarim-makineleri-ve-teknolojileri-muhendisligi": "Tarım Makineleri ve Teknolojileri Mühendisliği",
        "tarim-ticareti-ve-isletmeciligi": "Tarım Ticareti ve İşletmeciliği",
        "tarimsal-biyoteknoloji": "Tarımsal Biyoteknoloji",
        "tarimsal-genetik-muhendisligi": "Tarımsal Genetik Mühendisliği",
        "tarimsal-yapilar-ve-sulama": "Tarımsal Yapılar ve Sulama",
        "tarih-ogretmenligi": "Tarih Öğretmenliği",
        "tarih-oncesi-arkeolojisi": "Tarih Öncesi Arkeolojisi",
        "tarih": "Tarih",
        "tarla-bitkileri": "Tarla Bitkileri",
        "teknoloji-ve-bilgi-yonetimi": "Teknoloji ve Bilgi Yönetimi",
        "tekstil-muhendisligi": "Tekstil Mühendisliği",
        "tekstil-tasarimi": "Tekstil Tasarımı",
        "tekstil-ve-moda-tasarimi": "Tekstil ve Moda Tasarımı",
        "televizyon-haberciligi-ve-programciligi": "Televizyon Haberciliği ve Programcılığı",
        "tip-muhendisligi": "Tıp Mühendisliği",
        "tip": "Tıp",
        "tiyatro-elestirmenligi-ve-dramaturji": "Tiyatro Eleştirmenliği ve Dramaturji",
        "tohum-bilimi-ve-teknolojisi": "Tohum Bilimi ve Teknolojisi",
        "toprak-bilimi-ve-bitki-besleme": "Toprak Bilimi ve Bitki Besleme",
        "turizm-isletmeciligi": "Turizm İşletmeciliği",
        "turizm-rehberligi": "Turizm Rehberliği",
        "turizm-ve-otel-isletmeciligi": "Turizm ve Otel İşletmeciliği",
        "turk-dili-ve-edebiyati-ogretmenligi": "Türk Dili ve Edebiyatı Öğretmenliği",
        "turk-dili-ve-edebiyati": "Türk Dili ve Edebiyatı",
        "turk-halkbilimi": "Türk Halkbilimi",
        "turk-islam-arkeolojisi": "Türk İslam Arkeolojisi",
        "turkce-ogretmenligi": "Türkçe Öğretmenliği",
        "turkoloji": "Türkoloji",
        "tutun-eksperligi": "Tütün Eksperliği",
        "ucak-bakim-ve-onarim": "Uçak Bakım ve Onarım",
        "ucak-elektrik-ve-elektronigi": "Uçak Elektrik ve Elektroniği",
        "ucak-govde-ve-motor-bakimi": "Uçak Gövde ve Motor Bakımı",
        "ucak-muhendisligi": "Uçak Mühendisliği",
        "ukrayna-dili-ve-edebiyati": "Ukrayna Dili ve Edebiyatı",
        "uluslararasi-ekonomi": "Uluslararası Ekonomi",
        "uluslararasi-finans": "Uluslararası Finans",
        "uluslararasi-finans-ve-bankacilik": "Uluslararası Finans ve Bankacılık",
        "uluslararasi-girisimcilik": "Uluslararası Girişimcilik",
        "uluslararasi-iliskiler": "Uluslararası İlişkiler",
        "uluslararasi-isletme-yonetimi": "Uluslararası İşletme Yönetimi",
        "uluslararasi-tip": "Uluslararası Tıp",
        "uluslararasi-ticaret": "Uluslararası Ticaret",
        "uluslararasi-ticaret-ve-finans": "Uluslararası Ticaret ve Finans",
        "uluslararasi-ticaret-ve-finansman": "Uluslararası Ticaret ve Finansman",
        "uluslararasi-ticaret-ve-isletmecilik": "Uluslararası Ticaret ve İşletmecilik",
        "uluslararasi-ticaret-ve-lojistik": "Uluslararası Ticaret ve Lojistik",
        "uluslararasi-ulastirma-sistemleri": "Uluslararası Ulaştırma Sistemleri",
        "urdu-dili-ve-edebiyati": "Urdu Dili ve Edebiyatı",
        "uzay-bilimleri-ve-teknolojileri": "Uzay Bilimleri ve Teknolojileri",
        "uzay-muhendisligi": "Uzay Mühendisliği",
        "uzay-ve-uydu-muhendisligi": "Uzay ve Uydu Mühendisliği",
        "veri-bilimi-ve-analitigi": "Veri Bilimi ve Analitiği",
        "veteriner": "Veteriner",
        "yaban-hayati-ekolojisi-ve-yonetimi": "Yaban Hayatı Ekolojisi ve Yönetimi",
        "yapay-zeka-muhendisligi": "Yapay Zeka Mühendisliği",
        "yapay-zeka-ve-makine-ogrenmesi": "Yapay Zeka ve Makine Öğrenmesi",
        "yapay-zeka-ve-veri-muhendisligi": "Yapay Zeka ve Veri Mühendisliği",
        "yazilim-gelistirme": "Yazılım Geliştirme",
        "yazilim-muhendisligi": "Yazılım Mühendisliği",
        "yeni-medya": "Yeni Medya",
        "yeni-medya-ve-iletisim": "Yeni Medya ve İletişim",
        "yerel-yonetimler": "Yerel Yönetimler",
        "yiyecek-ve-icecek-isletmeciligi": "Yiyecek ve İçecek İşletmeciliği",
        "yonetim-bilimleri-programlari": "Yönetim Bilimleri Programları",
        "yonetim-bilisim-sistemleri": "Yönetim Bilişim Sistemleri",
        "yunan-dili-ve-edebiyati": "Yunan Dili ve Edebiyatı",
        "zaza-dili-ve-edebiyati": "Zaza Dili ve Edebiyatı",
        "ziraat-muhendisligi-programlari": "Ziraat Mühendisliği Programları",
        "zootekni": "Zootekni"
    }
    # Eğer sözlükte tanımladıysak tam adını çek, yoksa otomatik düzeltmeye çalış
    if meslek_link in sozluk:
        bölüm_adı = sozluk[meslek_link]
    else:
        # Yedek plan: Sözlükte yoksa tireleri boşluk yapıp arat
        bölüm_adı = meslek_link.replace("-", " ")
    
    # Sayfa Başlığı
    baslik = f"YKS {bölüm_adı} Taban Puanları ve Sıralamaları"
    
    col_bolum = get_valid_column_name('yks_taban_puanlari', ['bölüm', 'bolum', 'program', 'program_adi'])
    
    # SQL sorgumuz %...% esnekliğiyle arama yapar
    sorgu = f"SELECT * FROM yks_taban_puanlari WHERE {col_bolum} LIKE ?"
    veriler = db_query(sorgu, (f"%{bölüm_adı}%",))
    
    return render_template('index.html', veriler=veriler, sayfa_basligi=baslik, mevcut_meslek=meslek_link)
    
    return render_template('index.html', veriler=veriler, sayfa_basligi=baslik, mevcut_meslek=meslek_link)
# 1. ÖNCE ROTALARI YAZIYORUZ (app.run'ın yukarısında olmalı)

# Gizli Admin Paneli (Güncellenmiş Hali)
@app.route('/ataturk-kosesi/admin-panel')
def admin_panel():
    conn = sqlite3.connect('veritabani.db')
    cursor = conn.cursor()
    
    # 1. Sadece onay bekleyenleri getir
    cursor.execute("SELECT id, isim, not_metni FROM ataturk_notlari WHERE onayli = 0")
    bekleyenler = cursor.fetchall()
    
    # 2. Sitede şu an yayında/var olan onaylı mesajları getir
    cursor.execute("SELECT id, isim, not_metni FROM ataturk_notlari WHERE onayli = 1 ORDER BY id DESC")
    onaylananlar = cursor.fetchall()
    
    conn.close()
    
    # İki listeyi de HTML sayfasına gönderiyoruz
    return render_template('admin.html', notlar=bekleyenler, onayli_notlar=onaylananlar)

# Onayla/Sil İşlemi
@app.route('/ataturk-kosesi/islem/<int:not_id>/<string:aksiyon>')
def not_islem(not_id, aksiyon):
    conn = sqlite3.connect('veritabani.db')
    cursor = conn.cursor()
    if aksiyon == "onayla":
        cursor.execute("UPDATE ataturk_notlari SET onayli = 1 WHERE id = ?", (not_id,))
    elif aksiyon == "sil":
        cursor.execute("DELETE FROM ataturk_notlari WHERE id = ?", (not_id,))
    conn.commit()
    conn.close()
    return f"İşlem tamam! <a href='/ataturk-kosesi/admin-panel'>Geri dön</a>"


# 2. ROTALAR BİTTİKTEN SONRA DEBUG VE ÇALIŞTIRMA KODU (En altta kalmalı)

with app.app_context():
    print("\n--- FLASK TARAFINDAN KAYITLI TÜM ROTALAR ---")
    for rule in app.url_map.iter_rules():
        print(f"Rota: {rule.endpoint} -> {rule.rule}")
    print("-------------------------------------------\n")

if __name__ == '__main__':
    app.run(debug=True)
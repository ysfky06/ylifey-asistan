from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = "ysf_ultra_core_key_2026"

def veritabanini_kur():
    conn = sqlite3.connect('veritabanı.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eposta TEXT UNIQUE NOT NULL,
            sifre TEXT NOT NULL,
            is_premium INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mesajlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER,
            rol TEXT,
            icerik TEXT,
            karakter TEXT,
            FOREIGN KEY(kullanici_id) REFERENCES kullanicilar(id)
        )
    ''')
    conn.commit()
    conn.close()

veritabanini_kur()

# 🧠 ENGELLENMEYEN GÜVENLİ YAPAY ZEKA MOTORU
def yapay_zeka_istek_at(mesajlar_listesi):
    try:
        formatted_messages = []
        for msg in mesajlar_listesi:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})
            
        payload = {
            "messages": formatted_messages,
            "model": "openai",
            "jsonMode": False
        }
        
        headers = {"Content-Type": "application/json"}
        res = requests.post("https://text.pollinations.ai/", json=payload, headers=headers)
        
        if res.status_code == 200:
            return res.text.strip()
        else:
            return f"Yapay zeka motoru yanıt vermedi (Kod: {res.status_code})"
    except Exception as e:
        return f"Bağlantı Hatası: {e}"

@app.route('/', methods=['GET', 'POST'])
def ana_sayfa():
    if 'kullanici_id' not in session:
        return redirect(url_for('giris_yap'))

    kullanici_id = session['kullanici_id']
    
    conn = sqlite3.connect('veritabanı.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_premium, eposta FROM kullanicilar WHERE id = ?', (kullanici_id,))
    kullanici = cursor.fetchone()
    
    if not kullanici:
        conn.close()
        return redirect(url_for('giris_yap'))
        
    is_premium = kullanici[0] == 1
    eposta = kullanici[1]
    aktif_karakter = request.args.get('karakter', 'genel')

    if aktif_karakter == 'gorsel' and not is_premium:
        conn.close()
        return redirect(url_for('ana_sayfa', karakter='genel', hata='premium_gerekli'))

    if request.args.get('aksiyon') == 'temizle':
        cursor.execute('DELETE FROM mesajlar WHERE kullanici_id = ? AND karakter = ?', (kullanici_id, aktif_karakter))
        conn.commit()
        conn.close()
        return redirect(url_for('ana_sayfa', karakter=aktif_karakter))

    if request.method == 'POST':
        kullanici_yazisi = request.form.get('user_input')
        
        if kullanici_yazisi:
            cursor.execute('INSERT INTO mesajlar (kullanici_id, rol, icerik, karakter) VALUES (?, ?, ?, ?)', 
                           (kullanici_id, 'user', kullanici_yazisi, aktif_karakter))
            conn.commit()

            if aktif_karakter == 'gorsel':
                temiz_prompt = kullanici_yazisi.replace(" ", "%20")
                resim_url = f"https://image.pollinations.ai/prompt/{temiz_prompt}?width=1024&height=1024&nologo=true"
                resim_html_etiketi = f"__RESIM_LINKI__{resim_url}"
                cursor.execute('INSERT INTO mesajlar (kullanici_id, rol, icerik, karakter) VALUES (?, ?, ?, ?)', 
                               (kullanici_id, 'assistant', resim_html_etiketi, aktif_karakter))
                conn.commit()
            else:
                karakter_talimatlari = {
                    "genel": "Sen akıllı, pratik genel bir yapay zeka asistanısın.",
                    "yazilim": "Sen kıdemli bir yazılımcısın. Sadece optimize kodlar yazarsın. Kodları ``` içine al.",
                    "fitness": "Sen profesyonel bir fitness koçusun. Antrenman programları ve beslenme anlatırsın.",
                    "medya": "Sen sosyal medya uzmanısın. YouTube Shorts senaryoları ve başlıkları üretirsin."
                }
                
                sistem_orijinal = karakter_talimatlari.get(aktif_karakter, karakter_talimatlari["genel"])
                sistem_talimati = f"👑 PREMIUM MOD. {sistem_orijinal}" if is_premium else sistem_orijinal

                cursor.execute('SELECT rol, icerik FROM mesajlar WHERE kullanici_id = ? AND karakter = ? ORDER BY id ASC', (kullanici_id, aktif_karakter))
                gecmis_satirlar = cursor.fetchall()
                
                api_mesajlari = [{"role": "system", "content": sistem_talimati}]
                for rol, icerik in gecmis_satirlar:
                    api_mesajlari.append({"role": rol, "content": icerik})

                yapay_zekanin_cevabi = yapay_zeka_istek_at(api_mesajlari)
                
                cursor.execute('INSERT INTO mesajlar (kullanici_id, rol, icerik, karakter) VALUES (?, ?, ?, ?)', 
                               (kullanici_id, 'assistant', yapay_zekanin_cevabi, aktif_karakter))
                conn.commit()

    cursor.execute('SELECT rol, icerik FROM mesajlar WHERE kullanici_id = ? AND karakter = ? ORDER BY id ASC', (kullanici_id, aktif_karakter))
    sohbet_gecmisi = cursor.fetchall()
    conn.close()

    gosterilecek_hata = request.args.get('hata')
    return render_template('index.html', sohbet=sohbet_gecmisi, premium=is_premium, kullanici_adi=eposta, aktif_karakter=aktif_karakter, hata=gosterilecek_hata)

@app.route('/kayit', methods=['GET', 'POST'])
def kayit_ol():
    if request.method == 'POST':
        eposta = request.form.get('eposta')
        sifre = request.form.get('sifre')
        try:
            conn = sqlite3.connect('veritabanı.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO kullanicilar (eposta, sifre) VALUES (?, ?)', (eposta, sifre))
            conn.commit()
            conn.close()
            return redirect(url_for('giris_yap'))
        except sqlite3.IntegrityError:
            return "Bu e-posta adresi zaten kayıtlı!"
    return render_template('kayit.html')

@app.route('/giris', methods=['GET', 'POST'])
def giris_yap():
    if request.method == 'POST':
        eposta = request.form.get('eposta')
        sifre = request.form.get('sifre')
        conn = sqlite3.connect('veritabanı.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM kullanicilar WHERE eposta = ? AND sifre = ?', (eposta, sifre))
        kullanici = cursor.fetchone()
        conn.close()
        if kullanici:
            session['kullanici_id'] = kullanici[0]
            return redirect(url_for('ana_sayfa'))
        else:
            return "Hatalı e-posta veya şifre!"
    return render_template('giris.html')

@app.route('/cikis')
def cikis_yap():
    session.pop('kullanici_id', None)
    return redirect(url_for('giris_yap'))

@app.route('/premium-yap')
def premium_yap():
    if 'kullanici_id' in session:
        conn = sqlite3.connect('veritabanı.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE kullanicilar SET is_premium = 1 WHERE id = ?', (session['kullanici_id'],))
        conn.commit()
        conn.close()
    return redirect(url_for('ana_sayfa'))

if __name__ == '__main__':
    app.run(debug=True)
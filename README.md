# berber-randevu-sistemi

Django tabanli berber randevu ve yonetim paneli projesi.

## Ozellikler

- Randevu olusturma ve saat uygunluk kontrolu
- Berber paneli ile randevu yonetimi
- Coklu hizmet secimi ve fiyat hesaplama
- Iletisim formu ve SMTP uzerinden bildirim e-postalari
- Cok dilli icerik destegi (TR/EN/DE)

## Kurulum

1. Sanal ortam olustur ve aktif et:
   - Windows: `python -m venv venv && .\\venv\\Scripts\\activate`
2. Bagimliliklari yukle:
   - `pip install -r requirements.txt`
3. Ortam degiskenlerini hazirla:
   - `.env.example` dosyasini `.env` olarak kopyala ve degerleri duzenle.
4. Veritabani migrationlarini uygula:
   - `python manage.py migrate`
5. Uygulamayi baslat:
   - `python manage.py runserver`

## Guvenlik Notu

Bu repoda gizli bilgiler tutulmamaktadir. `SECRET_KEY`, SMTP kullanici adi/sifre gibi degerler ortam degiskenlerinden okunur.

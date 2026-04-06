# Berber Randevu Sistemi

Django ile gelistirilmis, cok dilli berber randevu ve yonetim paneli uygulamasi.

## Proje Ozeti

`berber-randevu-sistemi`, musterilerin online randevu alabilecegi ve isletmenin randevulari panel uzerinden yonetebilecegi bir web uygulamasidir.

## Ozellikler

- Online randevu olusturma ve uygun saat kontrolu
- Berber panelinden randevu listeleme, filtreleme ve durum guncelleme
- Coklu hizmet secimi ve toplam fiyat hesaplama
- Iletisim formu ve SMTP uzerinden e-posta bildirimleri
- Cok dilli arayuz destegi (TR/EN/DE)
- Django admin paneli ile icerik ve ayar yonetimi

## Kullanilan Teknolojiler

- Python 3
- Django 5.2
- SQLite (gelistirme ortami)
- HTML, CSS, JavaScript

## Yerel Kurulum

1. Depoyu klonlayin:
   - `git clone https://github.com/Samet-Batuhan/berber-randevu-sistemi.git`
   - `cd berber-randevu-sistemi`
2. Sanal ortami olusturun ve aktif edin:
   - Windows: `python -m venv venv`
   - Windows: `.\\venv\\Scripts\\activate`
3. Bagimliliklari yukleyin:
   - `pip install -r requirements.txt`
4. Ortam degiskenlerini hazirlayin:
   - `.env.example` dosyasini `.env` olarak kopyalayin
   - Gerekli degerleri kendi bilgilerinizle doldurun
5. Veritabani migrationlarini uygulayin:
   - `python manage.py migrate`
6. Uygulamayi calistirin:
   - `python manage.py runserver`

## Ortam Degiskenleri

Ornek degiskenler `.env.example` dosyasinda bulunur.

- `DJANGO_SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`

## Ekran Goruntuleri

- Ana Sayfa
![Ana Sayfa](docs/images/ana-sayfa.png)

- Randevu
![Randevu](docs/images/randevu.png)

- Fiyat Listesi
![Fiyat Listesi](docs/images/fiyat-listesi.png)

- Admin Paneli
![Admin Paneli](docs/images/admin-paneli.png)

## Guvenlik Notu

Bu repoda gizli bilgi tutulmaz. `SECRET_KEY` ve e-posta SMTP bilgileri ortam degiskenlerinden okunur.

## Lisans

Bu proje `MIT` lisansi ile paylasilmaktadir. Detaylar icin `LICENSE` dosyasina bakabilirsiniz.

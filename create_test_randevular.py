from datetime import datetime, time, date
from berber.models import Berber, Hizmet, Randevu

# Ali Demir berberini bul
try:
    berber = Berber.objects.get(ad__icontains='Ali')
    print(f"Berber bulundu: {berber.ad}")
except Berber.DoesNotExist:
    print("Ali Demir bulunamadi! Mevcut berberler:")
    for b in Berber.objects.filter(aktif=True):
        print(f"  - {b.ad}")
    import sys
    sys.exit()

# Aktif bir hizmet bul
hizmet = Hizmet.objects.filter(aktif=True).first()
print(f"Hizmet: {hizmet.ad}")

# 27 Ekim 2024 - Pazartesi
tarih = date(2024, 10, 27)
print(f"Tarih: {tarih}")

# Pazartesi: 09:00 - 19:00, 30 dakikalik araliklarla
saatler = []
for saat in range(9, 19):
    saatler.append(time(saat, 0))
    saatler.append(time(saat, 30))

print(f"Olusturulacak randevu sayisi: {len(saatler)}")

# Mevcut randevulari temizle
mevcut = Randevu.objects.filter(tarih=tarih, berber=berber)
if mevcut.exists():
    print(f"{mevcut.count()} mevcut randevu siliniyor...")
    mevcut.delete()

# Yeni randevular olustur
basarili = 0
for i, saat in enumerate(saatler, 1):
    randevu = Randevu.objects.create(
        ad=f"Test{i}",
        soyad="Musteri",
        telefon=f"+49 123 456{i:04d}",
        email=f"test{i}@example.com",
        berber=berber,
        tarih=tarih,
        saat=saat,
        notlar=f"Test randevusu {i}",
        durum='onaylandi'
    )
    randevu.hizmetler.add(hizmet)
    basarili += 1
    if i % 5 == 0:
        print(f"  {i}/{len(saatler)} randevu olusturuldu...")

print(f"\nToplam {basarili} randevu olusturuldu!")
print(f"\nSimdi randevu sayfasinda:")
print(f"  1. {berber.ad} secin")
print(f"  2. 27 Ekim'i secin")
print(f"  3. Takvimde 27 Ekim KIRMIZI olmali")
print(f"  4. Tum saatler 'DOLU' olmali")


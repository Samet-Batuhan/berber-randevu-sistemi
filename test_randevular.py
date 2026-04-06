#!/usr/bin/env python
"""Test randevuları oluşturma scripti"""
import os
import django
import random

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'berber_sitesi.settings')
django.setup()

from datetime import datetime, time, date
from berber.models import Berber, Hizmet, Randevu

# Ali Demir berberini bul
try:
    berber = Berber.objects.get(ad__icontains='Ali')
    print(f"✅ Berber bulundu: {berber.ad}")
except Berber.DoesNotExist:
    print("❌ Ali Demir bulunamadı!")
    print("Mevcut berberler:")
    for b in Berber.objects.filter(aktif=True):
        print(f"  - {b.ad}")
    exit()

# Tüm aktif hizmetleri al
hizmetler = list(Hizmet.objects.filter(aktif=True))
if not hizmetler:
    print("❌ Aktif hizmet bulunamadı!")
    exit()

print(f"✅ Toplam {len(hizmetler)} hizmet bulundu:")
for h in hizmetler:
    print(f"   - {h.ad} ({h.fiyat}€)")

# 27 Ekim 2024 - Pazartesi
tarih = date(2024, 10, 27)
print(f"📅 Tarih: {tarih} ({tarih.strftime('%A')})")

# Pazartesi çalışma saatleri: 09:00 - 19:00
# 30 dakikalık aralıklarla
saatler = []
for saat in range(9, 19):  # 09:00'dan 18:30'a kadar
    saatler.append(time(saat, 0))   # 09:00, 10:00, ...
    saatler.append(time(saat, 30))  # 09:30, 10:30, ...

print(f"⏰ Oluşturulacak randevu sayısı: {len(saatler)}")
print(f"⏰ Saatler: {saatler[0]} - {saatler[-1]}")

# Mevcut randevuları temizle
mevcut = Randevu.objects.filter(tarih=tarih, berber=berber)
if mevcut.exists():
    print(f"🗑️  {mevcut.count()} mevcut randevu siliniyor...")
    mevcut.delete()

# Yeni randevular oluştur
basarili = 0
for i, saat in enumerate(saatler, 1):
    try:
        # Rastgele 1-3 arası hizmet seç
        secilen_hizmetler = random.sample(hizmetler, random.randint(1, min(3, len(hizmetler))))
        
        randevu = Randevu.objects.create(
            ad=f"Test{i}",
            soyad="Müşteri",
            telefon=f"+49 123 456{i:04d}",
            email=f"test{i}@example.com",
            berber=berber,
            tarih=tarih,
            saat=saat,
            notlar=f"Test randevusu #{i}",
            durum='beklemede'  # Beklemede durumunda
        )
        
        # Önce randevuyu kaydet, sonra hizmetleri ekle
        randevu.save()
        
        # Rastgele seçilen hizmetleri ekle (ManyToMany için save sonrası)
        for hizmet in secilen_hizmetler:
            randevu.hizmetler.add(hizmet)
        
        hizmet_isimleri = ", ".join([h.ad for h in secilen_hizmetler])
        basarili += 1
        print(f"  ✅ {i}/{len(saatler)}: {saat} - {hizmet_isimleri}")
    except Exception as e:
        print(f"  ❌ {i}/{len(saatler)}: {saat} - HATA: {e}")

print(f"\n🎉 Toplam {basarili}/{len(saatler)} randevu oluşturuldu!")
print(f"\nŞimdi randevu sayfasında 27 Ekim'i seçin:")
print(f"  - Takvimde 27 Ekim KIRMIZI olmalı (tam dolu)")
print(f"  - Tüm saatler üstü çizili 'DOLU' yazmalı")


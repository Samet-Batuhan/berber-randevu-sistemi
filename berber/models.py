from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Berber(models.Model):
    """Berber modeli - berber bilgilerini tutar"""
    ad = models.CharField(max_length=100, verbose_name="Berber Adı")
    telefon = models.CharField(max_length=15, verbose_name="Telefon")
    email = models.EmailField(verbose_name="E-posta")
    adres = models.TextField(verbose_name="Adres")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    profil_foto = models.ImageField(upload_to='berberler/', blank=True, verbose_name="Profil Fotoğrafı")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Berber"
        verbose_name_plural = "Berberler"
        ordering = ['ad']

    def __str__(self):
        return self.ad


class Hizmet(models.Model):
    """Hizmet modeli - berber hizmetlerini tutar"""
    ad = models.CharField(max_length=100, verbose_name="Hizmet Adı")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    fiyat = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Fiyat")
    sure_dakika = models.PositiveIntegerField(verbose_name="Süre (Dakika)")
    sira = models.PositiveIntegerField(default=0, verbose_name="Sıra")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Hizmet"
        verbose_name_plural = "Hizmetler"
        ordering = ['sira', 'ad']

    def __str__(self):
        return f"{self.ad} - {self.fiyat}€"


class HizmetTranslation(models.Model):
    """Hizmet çevirileri - her hizmet için dil bazlı ad ve açıklama"""
    LANGUAGE_CHOICES = (
        ('tr', 'Türkçe'),
        ('en', 'English'),
        ('de', 'Deutsch'),
    )

    hizmet = models.ForeignKey(Hizmet, on_delete=models.CASCADE, related_name='translations', verbose_name="Hizmet")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, verbose_name="Dil")
    ad = models.CharField(max_length=150, blank=True, verbose_name="Çevrilmiş Ad")
    aciklama = models.TextField(blank=True, verbose_name="Çevrilmiş Açıklama")

    class Meta:
        unique_together = ('hizmet', 'language')
        verbose_name = "Hizmet Çeviri"
        verbose_name_plural = "Hizmet Çevirileri"

    def __str__(self):
        return f"{self.hizmet.ad} [{self.language}]"


@receiver(post_save, sender=Hizmet)
def create_or_update_hizmet_translations(sender, instance: Hizmet, created: bool, **kwargs):
    """Hizmet oluşturulduğunda EN/DE için otomatik çeviri kayıtları oluşturur/günceller."""
    try:
        # Döngü içinde import ederek dairesel bağımlılığı önle
        from .views import get_translation, get_service_description_translation
    except Exception:
        # View fonksiyonlarına erişilemezse, minimum fallback: kaynak metni kullan
        def get_translation(text, language):
            return text
        def get_service_description_translation(text, language):
            return text

    original_name = instance.ad or ""
    original_desc = instance.aciklama or ""

    for lang in ('en', 'de'):
        translated_name = get_translation(original_name, lang) or original_name
        translated_desc = get_service_description_translation(original_desc, lang) or original_desc
        HizmetTranslation.objects.update_or_create(
            hizmet=instance,
            language=lang,
            defaults={
                'ad': translated_name,
                'aciklama': translated_desc,
            }
        )


class Randevu(models.Model):
    """Randevu modeli - müşteri randevularını tutar"""
    DURUM_SECENEKLERI = [
        ('beklemede', 'Beklemede'),
        ('onaylandi', 'Onaylandı'),
        ('iptal', 'İptal'),
        ('tamamlandi', 'Tamamlandı'),
    ]
    # Alias for template compatibility
    DURUM_CHOICES = DURUM_SECENEKLERI

    # Müşteri bilgileri
    ad = models.CharField(max_length=50, verbose_name="Ad")
    soyad = models.CharField(max_length=50, verbose_name="Soyad")
    telefon = models.CharField(max_length=20, verbose_name="Telefon")  # Uluslararası format için genişletildi
    email = models.EmailField(verbose_name="E-posta")
    
    # Randevu bilgileri
    berber = models.ForeignKey(Berber, on_delete=models.CASCADE, verbose_name="Berber")
    hizmet = models.ForeignKey(Hizmet, on_delete=models.CASCADE, verbose_name="Hizmet", null=True, blank=True)  # Eski alan (backward compatibility)
    hizmetler = models.ManyToManyField(Hizmet, related_name='randevular', verbose_name="Hizmetler", blank=True)  # Yeni çoklu seçim
    tarih = models.DateField(verbose_name="Tarih")
    saat = models.TimeField(verbose_name="Saat")
    
    # Durum ve notlar
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='beklemede', verbose_name="Durum")
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    
    # Zaman damgaları
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Randevu"
        verbose_name_plural = "Randevular"
        ordering = ['-olusturma_tarihi']

    def __str__(self):
        return f"{self.ad} {self.soyad} - {self.tarih} {self.saat}"

    @property
    def toplam_fiyat(self):
        """Randevunun toplam fiyatını hesaplar"""
        # Yeni çoklu hizmet varsa onları topla
        if self.hizmetler.exists():
            return sum(h.fiyat for h in self.hizmetler.all())
        # Eski tek hizmet varsa onu kullan (backward compatibility)
        elif self.hizmet:
            return self.hizmet.fiyat
        return 0
    
    def get_hizmetler_listesi(self):
        """Seçili hizmetlerin listesini döndürür"""
        if self.hizmetler.exists():
            return list(self.hizmetler.all())
        elif self.hizmet:
            return [self.hizmet]
        return []

    @property
    def tam_ad(self):
        """Müşterinin tam adını döndürür"""
        return f"{self.ad} {self.soyad}"


class Galeri(models.Model):
    """Galeri modeli - berber fotoğraflarını tutar"""
    baslik = models.CharField(max_length=100, verbose_name="Başlık")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    foto = models.ImageField(upload_to='galeri/', verbose_name="Fotoğraf")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    sira = models.PositiveIntegerField(default=0, verbose_name="Sıra")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Galeri"
        verbose_name_plural = "Galeri"
        ordering = ['sira', '-olusturma_tarihi']

    def __str__(self):
        return self.baslik


class Iletisim(models.Model):
    """İletişim modeli - iletişim mesajlarını tutar"""
    ad = models.CharField(max_length=50, verbose_name="Ad")
    soyad = models.CharField(max_length=50, verbose_name="Soyad")
    email = models.EmailField(verbose_name="E-posta")
    telefon = models.CharField(max_length=20, verbose_name="Telefon")  # Uluslararası format için genişletildi
    konu = models.CharField(max_length=100, verbose_name="Konu")
    mesaj = models.TextField(verbose_name="Mesaj")
    okundu = models.BooleanField(default=False, verbose_name="Okundu")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "İletişim Mesajı"
        verbose_name_plural = "İletişim Mesajları"
        ordering = ['-olusturma_tarihi']

    def __str__(self):
        return f"{self.ad} {self.soyad} - {self.konu}"


class SiteAyarlari(models.Model):
    """Site ayarları modeli - genel site ayarlarını tutar"""
    site_adi = models.CharField(max_length=100, default="Berber Salonu", verbose_name="Site Adı")
    telefon = models.CharField(max_length=20, verbose_name="Cep Telefonu")
    dukkan_telefon = models.CharField(max_length=20, blank=True, verbose_name="Dükkan Telefonu")
    email = models.EmailField(verbose_name="E-posta (Sitede Görünen)", help_text="Müşterilerin göreceği e-posta adresi")
    adres = models.TextField(verbose_name="Adres")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    logo = models.ImageField(upload_to='site/', blank=True, verbose_name="Logo")
    favicon = models.ImageField(upload_to='site/', blank=True, verbose_name="Favicon")
    
    # Sosyal medya
    facebook = models.URLField(blank=True, verbose_name="Facebook")
    instagram = models.URLField(blank=True, verbose_name="Instagram")
    twitter = models.URLField(blank=True, verbose_name="Twitter")
    
    # Çalışma saatleri
    calisma_saatleri = models.TextField(verbose_name="Çalışma Saatleri")
    
    # Mail ayarları
    mail_host = models.CharField(
        max_length=100, 
        verbose_name="SMTP Sunucu", 
        help_text="Örn: smtp.gmail.com, smtp.web.de"
    )
    mail_port = models.PositiveIntegerField(
        default=587, 
        verbose_name="SMTP Port", 
        help_text="Genellikle 587 (TLS için)"
    )
    mail_username = models.CharField(
        max_length=100, 
        verbose_name="Yönetici Mail Adresi (SMTP)", 
        help_text="Randevu ve iletişim bildirimlerinin gönderileceği mail adresi (SMTP kullanıcı adı)"
    )
    mail_password = models.CharField(
        max_length=100, 
        verbose_name="App Password / Şifre", 
        help_text="Gmail için App Password, diğer sağlayıcılar için hesap şifresi"
    )
    mail_use_tls = models.BooleanField(
        default=True, 
        verbose_name="TLS Kullan", 
        help_text="Güvenli bağlantı için önerilir (genellikle işaretli olmalı)"
    )

    class Meta:
        verbose_name = "Site Ayarları"
        verbose_name_plural = "Site Ayarları"

    def __str__(self):
        return self.site_adi

    def save(self, *args, **kwargs):
        # Sadece bir tane site ayarları kaydı olmasını sağla
        if not self.pk and SiteAyarlari.objects.exists():
            return
        super().save(*args, **kwargs)
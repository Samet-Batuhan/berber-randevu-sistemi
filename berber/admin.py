from django.contrib import admin
from django.utils.html import format_html
from .models import Berber, Hizmet, Randevu, Galeri, Iletisim, SiteAyarlari, HizmetTranslation


@admin.register(Berber)
class BerberAdmin(admin.ModelAdmin):
    list_display = ['ad', 'telefon', 'email', 'aktif', 'olusturma_tarihi']
    list_filter = ['aktif', 'olusturma_tarihi']
    search_fields = ['ad', 'telefon', 'email']
    list_editable = ['aktif']
    ordering = ['ad']


class HizmetTranslationInline(admin.TabularInline):
    model = HizmetTranslation
    extra = 0
    fields = ['language', 'ad', 'aciklama']
    readonly_fields = ['language']
    
    def has_add_permission(self, request, obj=None):
        return False  # Otomatik oluşturuluyor, manuel ekleme yok
    
    def get_queryset(self, request):
        # Sadece EN ve DE çevirilerini göster
        return super().get_queryset(request).filter(language__in=['en', 'de'])
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Açıklama alanını daha büyük yap
        formset.form.base_fields['aciklama'].widget.attrs.update({
            'rows': 3,
            'cols': 40,
            'style': 'width: 100%;'
        })
        return formset


@admin.register(Hizmet)
class HizmetAdmin(admin.ModelAdmin):
    list_display = ['ad', 'fiyat', 'sure_dakika', 'sira', 'aktif', 'olusturma_tarihi']
    list_filter = ['aktif', 'olusturma_tarihi']
    search_fields = ['ad', 'aciklama']
    list_editable = ['fiyat', 'sure_dakika', 'sira', 'aktif']
    ordering = ['sira', 'ad']
    inlines = [HizmetTranslationInline]
    
    fieldsets = (
        ('Hizmet Bilgileri', {
            'fields': ('ad', 'aciklama', 'fiyat', 'sure_dakika', 'sira', 'aktif')
        }),
    )


@admin.register(Randevu)
class RandevuAdmin(admin.ModelAdmin):
    list_display = ['tam_ad', 'telefon', 'berber', 'get_hizmetler', 'get_toplam_fiyat', 'tarih', 'saat', 'durum', 'olusturma_tarihi']
    list_filter = ['durum', 'tarih', 'berber', 'olusturma_tarihi']
    search_fields = ['ad', 'soyad', 'telefon', 'email']
    list_editable = ['durum']
    ordering = ['-olusturma_tarihi']
    date_hierarchy = 'tarih'
    
    def get_hizmetler(self, obj):
        """Seçili hizmetleri göster"""
        hizmetler = obj.hizmetler.all()
        if hizmetler:
            return ", ".join([h.ad for h in hizmetler])
        return "-"
    get_hizmetler.short_description = 'Hizmetler'
    
    def get_toplam_fiyat(self, obj):
        """Toplam fiyatı göster"""
        return f"{obj.toplam_fiyat}€"
    get_toplam_fiyat.short_description = 'Toplam Fiyat'
    
    fieldsets = (
        ('Müşteri Bilgileri', {
            'fields': ('ad', 'soyad', 'telefon', 'email')
        }),
        ('Randevu Bilgileri', {
            'fields': ('berber', 'hizmetler', 'tarih', 'saat', 'durum')
        }),
        ('Notlar', {
            'fields': ('notlar',),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('hizmetler',)  # Çoklu seçim için güzel bir widget


@admin.register(Galeri)
class GaleriAdmin(admin.ModelAdmin):
    list_display = ['baslik', 'sira', 'aktif', 'olusturma_tarihi']
    list_filter = ['aktif', 'olusturma_tarihi']
    search_fields = ['baslik', 'aciklama']
    list_editable = ['sira', 'aktif']
    ordering = ['sira', '-olusturma_tarihi']


@admin.register(Iletisim)
class IletisimAdmin(admin.ModelAdmin):
    list_display = ['ad', 'soyad', 'email', 'konu', 'okundu', 'olusturma_tarihi']
    list_filter = ['okundu', 'olusturma_tarihi']
    search_fields = ['ad', 'soyad', 'email', 'konu']
    list_editable = ['okundu']
    ordering = ['-olusturma_tarihi']
    
    def get_queryset(self, request):
        # Okunmamış mesajları üstte göster
        return super().get_queryset(request).order_by('okundu', '-olusturma_tarihi')
    
    def changelist_view(self, request, extra_context=None):
        # Okunmamış mesaj sayısını ekle
        extra_context = extra_context or {}
        extra_context['okunmamis_mesaj_sayisi'] = Iletisim.objects.filter(okundu=False).count()
        return super().changelist_view(request, extra_context)
    
    fieldsets = (
        ('Kişi Bilgileri', {
            'fields': ('ad', 'soyad', 'telefon', 'email')
        }),
        ('Mesaj', {
            'fields': ('konu', 'mesaj', 'okundu')
        }),
    )


@admin.register(SiteAyarlari)
class SiteAyarlariAdmin(admin.ModelAdmin):
    list_display = ['site_adi', 'telefon', 'dukkan_telefon', 'email', 'mail_username']
    search_fields = ['site_adi', 'telefon', 'dukkan_telefon', 'email', 'mail_username']
    
    # Form widget'larını özelleştir
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Adres için textarea boyutunu ayarla
        form.base_fields['adres'].widget.attrs.update({
            'rows': 4,
            'style': 'width: 60%;'
        })
        form.base_fields['adres'].help_text = (
            '<br><strong>Adresi satır satır yazabilirsiniz. Örnek:</strong><br>'
            'Sokak/Cadde<br>'
            'Mahalle<br>'
            'İlçe/Şehir<br>'
            'Posta Kodu'
        )
        
        # Çalışma saatleri için yardım metni ekle
        form.base_fields['calisma_saatleri'].help_text = (
            '<br><strong>Her günü yeni satıra yazın. Örnek:</strong><br>'
            'Pazartesi : 09:00 - 19:00<br>'
            'Salı : Kapalı<br>'
            'Çarşamba : 09:00 - 19:00<br>'
            'Perşembe : 09:00 - 19:00<br>'
            'Cuma : 09:00 - 19:00<br>'
            'Cumartesi : 09:00 - 16:00<br>'
            'Pazar: Kapalı'
        )
        # Textarea boyutunu ayarla
        form.base_fields['calisma_saatleri'].widget.attrs.update({
            'rows': 8,
            'style': 'width: 60%; font-family: monospace;'
        })
        return form
    
    fieldsets = (
        ('Genel Bilgiler', {
            'fields': ('site_adi', 'telefon', 'dukkan_telefon', 'email', 'adres', 'aciklama', 'calisma_saatleri'),
            'description': '<strong>ℹ️ E-posta:</strong> Sitede gösterilecek mail adresi (footer, iletişim sayfası vb.)'
        }),
        ('Görsel', {
            'fields': ('logo', 'favicon')
        }),
        ('Sosyal Medya', {
            'fields': ('facebook', 'instagram', 'twitter')
        }),
        ('Mail Ayarları (SMTP)', {
            'fields': ('mail_username', 'mail_password', 'mail_host', 'mail_port', 'mail_use_tls'),
            'classes': ('collapse',),
            'description': '<strong>⚠️ Mail gönderimi için SMTP ayarlarını yapılandırın.</strong><br>'
                          '<strong>Yönetici Mail Adresi:</strong> Randevu ve iletişim bildirimlerinin GÖNDERİLECEĞİ mail adresi<br>'
                          '<strong>Örnek Web.de:</strong> smtp.web.de (Port: 587)<br>'
                          '<strong>Örnek Gmail:</strong> smtp.gmail.com (Port: 587)<br>'
                          '<strong>App Password:</strong> Email sağlayıcınızdan aldığınız özel şifre'
        }),
    )
    
    def has_add_permission(self, request):
        # Sadece bir tane site ayarları kaydı olmasını sağla
        return not SiteAyarlari.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Site ayarlarını silmeyi engelle
        return False


@admin.register(HizmetTranslation)
class HizmetTranslationAdmin(admin.ModelAdmin):
    list_display = ['hizmet', 'language', 'ad', 'aciklama', 'turkce_karsiligi']
    list_filter = ['language', 'hizmet__aktif']
    search_fields = ['hizmet__ad', 'ad', 'aciklama']
    list_editable = ['ad', 'aciklama']
    ordering = ['hizmet__ad', 'language']
    
    
    def turkce_karsiligi(self, obj):
        """Türkçe karşılığını göster"""
        return f"{obj.hizmet.ad} - {obj.hizmet.aciklama[:30]}..." if obj.hizmet.aciklama else obj.hizmet.ad
    turkce_karsiligi.short_description = "Türkçe Karşılığı"
    
    fieldsets = (
        ('Çeviri Bilgileri', {
            'fields': ('hizmet', 'language', 'ad', 'aciklama')
        }),
    )
    
    def get_queryset(self, request):
        # Sadece EN ve DE çevirilerini göster
        return super().get_queryset(request).filter(language__in=['en', 'de'])
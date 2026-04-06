from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMessage, get_connection
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, date, time
import json

from .models import Berber, Hizmet, Randevu, Galeri, Iletisim, SiteAyarlari, HizmetTranslation
from .forms import RandevuForm, IletisimForm


# ==================== MAIL GÖNDERIM FONKSİYONU ====================

def send_email_with_site_settings(subject, message, recipient_list):
    """
    Site Ayarları'ndaki SMTP bilgilerini kullanarak mail gönderir.
    
    Args:
        subject (str): Mail konusu
        message (str): Mail içeriği
        recipient_list (list): Alıcı mail adresleri listesi
    
    Returns:
        bool: Mail gönderimi başarılı ise True, değilse False
    """
    try:
        site_ayarlari = SiteAyarlari.objects.first()
        
        if not site_ayarlari:
            print("⚠️ Site Ayarları bulunamadı. Mail gönderilemedi.")
            return False
        
        # SMTP ayarlarını kontrol et
        if not site_ayarlari.mail_host or not site_ayarlari.mail_username or not site_ayarlari.mail_password:
            print("⚠️ Mail ayarları eksik. Admin panelinden SMTP ayarlarını yapılandırın.")
            return False
        
        # Özel SMTP bağlantısı oluştur
        connection = get_connection(
            host=site_ayarlari.mail_host,
            port=site_ayarlari.mail_port,
            username=site_ayarlari.mail_username,
            password=site_ayarlari.mail_password,
            use_tls=site_ayarlari.mail_use_tls,
        )
        
        # Email oluştur
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=site_ayarlari.mail_username,  # Admin panelindeki mail adresi
            to=recipient_list,
            connection=connection
        )
        
        # Mail gönder
        email.send(fail_silently=False)
        print(f"✅ Mail başarıyla gönderildi: {recipient_list}")
        return True
        
    except Exception as e:
        print(f"❌ Mail gönderim hatası: {e}")
        return False


# Çeviri sözlükleri
TRANSLATIONS = {
    'de': {
        'Berber Salonu': 'Friseursalon',
        'Ana Sayfa': 'Startseite',
        'Randevu Al': 'Termin vereinbaren',
        'Fiyat Listesi': 'Preisliste',
        'Galeri': 'Galerie',
        'İletişim': 'Kontakt',
        'Panel': 'Panel',
        'Dil': 'Sprache',
        'Sosyal Medya': 'Soziale Medien',
        'Çalışma Saatleri:': 'Öffnungszeiten:',
        'Pazartesi - Cumartesi: 09:00 - 19:00': 'Montag - Samstag: 09:00 - 19:00',
        'Pazartesi - Cumartesi: 09:00 - 19:00 Pazar: Kapalı': 'Montag - Samstag: 09:00 - 19:00 Sonntag: Geschlossen',
        'Pazartesi : 09:00 - 19:00\nSalı : Kapalı\nÇarşamba : 09:00 - 19:00\nPerşembe : 09:00 - 19:00\nCuma : 09:00 - 19:00\nCumartesi : 09:00 - 16:00\nPazar: Kapalı': 'Montag : 09:00 - 19:00\nDienstag : Geschlossen\nMittwoch : 09:00 - 19:00\nDonnerstag : 09:00 - 19:00\nFreitag : 09:00 - 19:00\nSamstag : 09:00 - 16:00\nSonntag: Geschlossen',
        'Tüm hakları saklıdır.': 'Alle Rechte vorbehalten.',
        'Hizmetlerimiz': 'Unsere Dienstleistungen',
        'Size özel profesyonel berber hizmetleri': 'Professionelle Friseurdienstleistungen speziell für Sie',
        'dakika': 'Minuten',
        'Detaylar': 'Details',
        'Berberlerimiz': 'Unsere Friseure',
        'Deneyimli ve profesyonel ekibimiz': 'Unser erfahrenes und professionelles Team',
        'Profesyonel Berber': 'Professioneller Friseur',
        'Profil': 'Profil',
        'Deneyimli berber': 'Erfahrener Friseur',
        '15 yıllık deneyime sahip, modern saç kesimi ve sakal bakımında uzman. Müşteri memnuniyeti odaklı çalışır.': '15 Jahre Erfahrung, Spezialist für moderne Haarschnitte und Bartpflege. Kundenorientiert.',
        'Genç ve dinamik yaklaşımıyla modern saç trendlerini takip eder. Müşteri odaklı hizmet anlayışı.': 'Verfolgt moderne Haartrends mit einem jungen und dynamischen Ansatz. Kundenorientierter Service.',
        'Klasik ve modern saç modellerinde uzman. Özellikle sakal şekillendirme konusunda deneyimli.': 'Spezialist für klassische und moderne Frisuren. Besonders erfahren in der Bartgestaltung.',
        'Çalışmalarımızdan örnekler': 'Beispiele unserer Arbeiten',
        'Tüm Galeri': 'Alle Galerie',
        'Randevu Almak İçin Hemen İletişime Geçin!': 'Kontaktieren Sie uns sofort für einen Termin!',
        'Profesyonel hizmetimizden yararlanmak için hemen randevu alın.': 'Nutzen Sie unseren professionellen Service und vereinbaren Sie sofort einen Termin.',
        'Profesyonel berber hizmetleri ile en iyi görünümünüzü ortaya çıkarın. Deneyimli ekibimiz ve modern tekniklerimizle hizmetinizdeyiz.': 'Bringen Sie Ihr bestes Aussehen mit professionellen Friseurdienstleistungen zur Geltung. Wir stehen Ihnen mit unserem erfahrenen Team und modernen Techniken zur Verfügung.',
        'Profesyonel berber hizmetleri ile en iyi görünümünüzü ortaya çıkarın.': 'Bringen Sie Ihr bestes Aussehen mit professionellen Friseurdienstleistungen zur Geltung.',
        'Salonumuz': 'Unser Salon',
        'Modern ve konforlu ortamımızı keşfedin': 'Entdecken Sie unsere moderne und komfortable Umgebung',
        'Tarayıcınız video oynatmayı desteklemiyor.': 'Ihr Browser unterstützt die Videowiedergabe nicht.',
        
        # Hizmet çevirileri
        'Klasik Saç Kesimi': 'Klassischer Haarschnitt',
        'Geleneksel berber kesimi ile temiz ve düzenli görünüm. Yıkama, kesim ve şekillendirme dahil.': 'Sauberes und ordentliches Aussehen mit traditionellem Friseurschnitt. Waschen, Schneiden und Styling inbegriffen.',
        'Modern Saç Kesimi': 'Moderner Haarschnitt',
        'Güncel trendlere uygun modern saç kesimi. Yıkama, kesim, şekillendirme ve styling dahil.': 'Moderner Haarschnitt nach aktuellen Trends. Waschen, Schneiden, Styling und Styling inbegriffen.',
        'Premium Paket': 'Premium-Paket',
        'Saç kesimi, sakal bakımı, yüz bakımı, masaj. Tam hizmet paketi.': 'Haarschnitt, Bartpflege, Gesichtspflege, Massage. Vollservice-Paket.',
        'Sakal Boyama': 'Bartfärbung',
        'Gri sakalları doğal renge boyama hizmeti. Kaliteli boyalar kullanılır.': 'Service zum Färben grauer Bärte in natürliche Farbe. Hochwertige Farben werden verwendet.',
        'Sakal Kesimi': 'Bartschneiden',
        'Profesyonel sakal kesimi ve şekillendirme. Temizlik ve bakım dahil.': 'Professionelles Bartschneiden und -styling. Reinigung und Pflege inbegriffen.',
        'Saç + Sakal Paketi': 'Haar + Bart Paket',
        'Saç kesimi ve sakal bakımının bir arada yapıldığı ekonomik paket. Yıkama ve şekillendirme dahil.': 'Wirtschaftliches Paket mit Haarschnitt und Bartpflege zusammen. Waschen und Styling inbegriffen.',
        
        # Form alanları
        'Ad': 'Vorname',
        'Soyad': 'Nachname',
        'Telefon': 'Telefon',
        'Cep Telefonu': 'Mobiltelefon',
        'Dükkan Telefonu': 'Festnetz',
        'E-posta': 'E-Mail',
        'Berber': 'Friseur',
        'Hizmet': 'Dienstleistung',
        'Tarih': 'Datum',
        'Saat': 'Uhrzeit',
        'Notlar': 'Notizen',
        'Konu': 'Betreff',
        'Mesaj': 'Nachricht',
        'Adres': 'Adresse',
        
        # Placeholder'lar
        'Adınız': 'Ihr Vorname',
        'Soyadınız': 'Ihr Nachname',
        'Telefon numaranız': 'Ihre Telefonnummer',
        'E-posta adresiniz': 'Ihre E-Mail-Adresse',
        'Ek notlarınız (opsiyonel)': 'Zusätzliche Notizen (optional)',
        'Mesaj konusu': 'Nachrichtenbetreff',
        'Mesajınız': 'Ihre Nachricht',
        'Saat seçiniz': 'Uhrzeit wählen',
        
        # Sayfa başlıkları ve metinler
        'Kişisel Bilgiler': 'Persönliche Daten',
        'Randevu Bilgileri': 'Termindaten',
        'Seçilen Hizmet:': 'Gewählte Dienstleistung:',
        'Fiyat:': 'Preis:',
        'Süre:': 'Dauer:',
        'Profesyonel berber hizmetlerimizin şeffaf fiyatları': 'Transparente Preise unserer professionellen Friseurdienstleistungen',
        'Hizmet Fiyatlarımız': 'Unsere Dienstleistungspreise',
        'Kaliteli hizmet, uygun fiyat': 'Qualitätsservice zu fairen Preisen',
        'Henüz hizmet eklenmemiş': 'Noch keine Dienstleistungen hinzugefügt',
        'Fiyat listesi yakında eklenecek.': 'Preisliste wird bald hinzugefügt.',
        'Çalışmalarımızdan örnekler ve profesyonel hizmetimizin kalitesi': 'Beispiele unserer Arbeiten und die Qualität unseres professionellen Services',
        'Profesyonel ekibimizin elinden çıkan eserler': 'Werke unserer professionellen Mannschaft',
        'Henüz fotoğraf eklenmemiş': 'Noch keine Fotos hinzugefügt',
        'Galeri yakında eklenecek.': 'Galerie wird bald hinzugefügt.',
        'Kendi Görünümünüzü Değiştirin!': 'Verändern Sie Ihr Aussehen!',
        'Bizimle iletişime geçin, sorularınızı sorun': 'Kontaktieren Sie uns, stellen Sie Ihre Fragen',
        'Mesaj Gönder': 'Nachricht senden',
        'İletişim Bilgileri': 'Kontaktinformationen',
        'İletişim bilgileri henüz eklenmemiş.': 'Kontaktinformationen noch nicht hinzugefügt.',
        'Konumumuz': 'Unsere Lage',
        'Hemen Randevu Alın!': 'Vereinbaren Sie sofort einen Termin!',
        'Çalışma Saatleri': 'Öffnungszeiten',
        'Profesyonel berber hizmeti': 'Professioneller Friseurservice',
        'Henüz hizmet eklenmemiş': 'Noch keine Dienstleistungen hinzugefügt',
        'Hizmetlerimiz yakında eklenecek.': 'Unsere Dienstleistungen werden bald hinzugefügt.',
        'Hizmetler': 'Dienstleistungen',
        'Seçilen Hizmetler:': 'Gewählte Dienstleistungen:',
        'Toplam Fiyat:': 'Gesamtpreis:',
        'Toplam Süre:': 'Gesamtdauer:',
        'Randevu Özeti': 'Terminübersicht',
        'Wählen Sie eine Uhrzeit für': 'Wählen Sie eine Uhrzeit für',
        'Randevunuz başarıyla alındı! Size e-posta ile bilgi verilecektir.': 'Ihr Termin wurde erfolgreich gebucht! Sie erhalten eine E-Mail-Bestätigung.',
        'Başarılı!': 'Erfolgreich!',
        'Hata!': 'Fehler!',
        'Uyarı!': 'Warnung!',
        'Bilgi': 'Information',
        'Mesajınız başarıyla gönderildi! En kısa sürede size dönüş yapacağız.': 'Ihre Nachricht wurde erfolgreich gesendet! Wir werden uns so schnell wie möglich bei Ihnen melden.',
        
        # Günler
        'Pazartesi': 'Montag',
        'Salı': 'Dienstag',
        'Çarşamba': 'Mittwoch',
        'Perşembe': 'Donnerstag',
        'Cuma': 'Freitag',
        'Cumartesi': 'Samstag',
        'Pazar': 'Sonntag',
        'Kapalı': 'Geschlossen',
    },
    'en': {
        'Berber Salonu': 'Barber Shop',
        'Ana Sayfa': 'Home',
        'Randevu Al': 'Book Appointment',
        'Fiyat Listesi': 'Price List',
        'Galeri': 'Gallery',
        'İletişim': 'Contact',
        'Panel': 'Panel',
        'Dil': 'Language',
        'Sosyal Medya': 'Social Media',
        'Çalışma Saatleri:': 'Working Hours:',
        'Pazartesi - Cumartesi: 09:00 - 19:00': 'Monday - Saturday: 09:00 - 19:00',
        'Pazartesi - Cumartesi: 09:00 - 19:00 Pazar: Kapalı': 'Monday - Saturday: 09:00 - 19:00 Sunday: Closed',
        'Pazartesi : 09:00 - 19:00\nSalı : Kapalı\nÇarşamba : 09:00 - 19:00\nPerşembe : 09:00 - 19:00\nCuma : 09:00 - 19:00\nCumartesi : 09:00 - 16:00\nPazar: Kapalı': 'Monday : 09:00 - 19:00\nTuesday : Closed\nWednesday : 09:00 - 19:00\nThursday : 09:00 - 19:00\nFriday : 09:00 - 19:00\nSaturday : 09:00 - 16:00\nSunday: Closed',
        'Tüm hakları saklıdır.': 'All rights reserved.',
        'Hizmetlerimiz': 'Our Services',
        'Size özel profesyonel berber hizmetleri': 'Professional barber services tailored for you',
        'dakika': 'minutes',
        'Detaylar': 'Details',
        'Berberlerimiz': 'Our Barbers',
        'Deneyimli ve profesyonel ekibimiz': 'Our experienced and professional team',
        'Profesyonel Berber': 'Professional Barber',
        'Profil': 'Profile',
        'Deneyimli berber': 'Experienced barber',
        '15 yıllık deneyime sahip, modern saç kesimi ve sakal bakımında uzman. Müşteri memnuniyeti odaklı çalışır.': '15 years of experience, specialist in modern haircuts and beard care. Customer satisfaction oriented.',
        'Genç ve dinamik yaklaşımıyla modern saç trendlerini takip eder. Müşteri odaklı hizmet anlayışı.': 'Follows modern hair trends with a young and dynamic approach. Customer-oriented service.',
        'Klasik ve modern saç modellerinde uzman. Özellikle sakal şekillendirme konusunda deneyimli.': 'Expert in classic and modern hairstyles. Especially experienced in beard shaping.',
        'Çalışmalarımızdan örnekler': 'Examples of our work',
        'Tüm Galeri': 'All Gallery',
        'Randevu Almak İçin Hemen İletişime Geçin!': 'Contact Us Immediately to Book an Appointment!',
        'Profesyonel hizmetimizden yararlanmak için hemen randevu alın.': 'Take advantage of our professional service and book an appointment immediately.',
        'Profesyonel berber hizmetleri ile en iyi görünümünüzü ortaya çıkarın. Deneyimli ekibimiz ve modern tekniklerimizle hizmetinizdeyiz.': 'Bring out your best look with professional barber services. We are at your service with our experienced team and modern techniques.',
        'Profesyonel berber hizmetleri ile en iyi görünümünüzü ortaya çıkarın.': 'Bring out your best look with professional barber services.',
        'Salonumuz': 'Our Salon',
        'Modern ve konforlu ortamımızı keşfedin': 'Discover our modern and comfortable environment',
        'Tarayıcınız video oynatmayı desteklemiyor.': 'Your browser does not support video playback.',
        
        # Hizmet çevirileri
        'Klasik Saç Kesimi': 'Classic Haircut',
        'Geleneksel berber kesimi ile temiz ve düzenli görünüm. Yıkama, kesim ve şekillendirme dahil.': 'Clean and neat appearance with traditional barber cut. Includes washing, cutting and styling.',
        'Modern Saç Kesimi': 'Modern Haircut',
        'Güncel trendlere uygun modern saç kesimi. Yıkama, kesim, şekillendirme ve styling dahil.': 'Modern haircut according to current trends. Includes washing, cutting, styling and styling.',
        'Premium Paket': 'Premium Package',
        'Saç kesimi, sakal bakımı, yüz bakımı, masaj. Tam hizmet paketi.': 'Haircut, beard care, facial care, massage. Full service package.',
        'Sakal Boyama': 'Beard Coloring',
        'Gri sakalları doğal renge boyama hizmeti. Kaliteli boyalar kullanılır.': 'Service for coloring gray beards to natural color. Quality dyes are used.',
        'Sakal Kesimi': 'Beard Cutting',
        'Profesyonel sakal kesimi ve şekillendirme. Temizlik ve bakım dahil.': 'Professional beard cutting and styling. Includes cleaning and care.',
        'Saç + Sakal Paketi': 'Hair + Beard Package',
        'Saç kesimi ve sakal bakımının bir arada yapıldığı ekonomik paket. Yıkama ve şekillendirme dahil.': 'Economic package where haircut and beard care are done together. Includes washing and styling.',
        
        # Form alanları
        'Ad': 'Name',
        'Soyad': 'Surname',
        'Telefon': 'Phone',
        'Cep Telefonu': 'Mobile Phone',
        'Dükkan Telefonu': 'Shop Phone',
        'E-posta': 'Email',
        'Berber': 'Barber',
        'Hizmet': 'Service',
        'Tarih': 'Date',
        'Saat': 'Time',
        'Notlar': 'Notes',
        'Konu': 'Subject',
        'Mesaj': 'Message',
        'Adres': 'Address',
        
        # Placeholder'lar
        'Adınız': 'Your name',
        'Soyadınız': 'Your surname',
        'Telefon numaranız': 'Your phone number',
        'E-posta adresiniz': 'Your email address',
        'Ek notlarınız (opsiyonel)': 'Additional notes (optional)',
        'Mesaj konusu': 'Message subject',
        'Mesajınız': 'Your message',
        'Saat seçiniz': 'Select time',
        
        # Sayfa başlıkları ve metinler
        'Kişisel Bilgiler': 'Personal Information',
        'Randevu Bilgileri': 'Appointment Information',
        'Seçilen Hizmet:': 'Selected Service:',
        'Fiyat:': 'Price:',
        'Süre:': 'Duration:',
        'Profesyonel berber hizmetlerimizin şeffaf fiyatları': 'Transparent prices of our professional barber services',
        'Hizmet Fiyatlarımız': 'Our Service Prices',
        'Kaliteli hizmet, uygun fiyat': 'Quality service, affordable price',
        'Henüz hizmet eklenmemiş': 'No services added yet',
        'Fiyat listesi yakında eklenecek.': 'Price list will be added soon.',
        'Çalışmalarımızdan örnekler ve profesyonel hizmetimizin kalitesi': 'Examples of our work and the quality of our professional service',
        'Profesyonel ekibimizin elinden çıkan eserler': 'Works from our professional team',
        'Henüz fotoğraf eklenmemiş': 'No photos added yet',
        'Galeri yakında eklenecek.': 'Gallery will be added soon.',
        'Kendi Görünümünüzü Değiştirin!': 'Change Your Look!',
        'Bizimle iletişime geçin, sorularınızı sorun': 'Contact us, ask your questions',
        'Mesaj Gönder': 'Send Message',
        'İletişim Bilgileri': 'Contact Information',
        'İletişim bilgileri henüz eklenmemiş.': 'Contact information not added yet.',
        'Konumumuz': 'Our Location',
        'Hemen Randevu Alın!': 'Book Appointment Now!',
        'Çalışma Saatleri': 'Working Hours',
        'Profesyonel berber hizmeti': 'Professional barber service',
        'Henüz hizmet eklenmemiş': 'No services added yet',
        'Hizmetlerimiz yakında eklenecek.': 'Our services will be added soon.',
        'Hizmetler': 'Services',
        'Seçilen Hizmetler:': 'Selected Services:',
        'Toplam Fiyat:': 'Total Price:',
        'Toplam Süre:': 'Total Duration:',
        'Randevu Özeti': 'Appointment Summary',
        'Wählen Sie eine Uhrzeit für': 'Select a time for',
        'Randevunuz başarıyla alındı! Size e-posta ile bilgi verilecektir.': 'Your appointment has been successfully booked! You will receive an email confirmation.',
        'Başarılı!': 'Success!',
        'Hata!': 'Error!',
        'Uyarı!': 'Warning!',
        'Bilgi': 'Information',
        'Mesajınız başarıyla gönderildi! En kısa sürede size dönüş yapacağız.': 'Your message has been sent successfully! We will get back to you as soon as possible.',
        
        # Günler
        'Pazartesi': 'Monday',
        'Salı': 'Tuesday',
        'Çarşamba': 'Wednesday',
        'Perşembe': 'Thursday',
        'Cuma': 'Friday',
        'Cumartesi': 'Saturday',
        'Pazar': 'Sunday',
        'Kapalı': 'Closed',
    },
    'tr': {
        # Türkçe için çeviri gerekmez, orijinal metinler kullanılır
        'Wählen Sie eine Uhrzeit für': 'Bir saat seçin',
    }
}

def set_language(request):
    """Dil değiştirme view'ı"""
    if request.method == 'POST':
        language = request.POST.get('language', 'de')
        if language in ['de', 'tr', 'en']:
            request.session['language'] = language
    return redirect(request.META.get('HTTP_REFERER', '/'))

def get_translation(text, language):
    """Metni çevir"""
    if not text:
        return text
    
    # Önce tam eşleşme ara
    if language in TRANSLATIONS and text in TRANSLATIONS[language]:
        return TRANSLATIONS[language][text]
    
    # Eğer tam eşleşme yoksa, benzer metinleri ara
    if language in TRANSLATIONS:
        for key, value in TRANSLATIONS[language].items():
            if text.lower() in key.lower() or key.lower() in text.lower():
                return value
    
    # Hizmet adları için genel çeviriler
    if language == 'en':
        if 'saç' in text.lower() and 'kesim' in text.lower():
            if 'klasik' in text.lower():
                return 'Classic Haircut'
            elif 'modern' in text.lower():
                return 'Modern Haircut'
            elif 'çocuk' in text.lower():
                return 'Children Haircut'
        elif 'sakal' in text.lower():
            if 'boyama' in text.lower():
                return 'Beard Coloring'
            elif 'kesim' in text.lower():
                return 'Beard Cutting'
        elif 'paket' in text.lower():
            if 'premium' in text.lower():
                return 'Premium Package'
            elif 'saç' in text.lower() and 'sakal' in text.lower():
                return 'Hair + Beard Package'
        elif 'yıkama' in text.lower() and 'styling' in text.lower():
            return 'Hair Washing + Styling'
    
    elif language == 'de':
        if 'saç' in text.lower() and 'kesim' in text.lower():
            if 'klasik' in text.lower():
                return 'Klassischer Haarschnitt'
            elif 'modern' in text.lower():
                return 'Moderner Haarschnitt'
            elif 'çocuk' in text.lower():
                return 'Kinderhaarschnitt'
        elif 'sakal' in text.lower():
            if 'boyama' in text.lower():
                return 'Bartfärbung'
            elif 'kesim' in text.lower():
                return 'Bartschneiden'
        elif 'paket' in text.lower():
            if 'premium' in text.lower():
                return 'Premium-Paket'
            elif 'saç' in text.lower() and 'sakal' in text.lower():
                return 'Haar + Bart Paket'
        elif 'yıkama' in text.lower() and 'styling' in text.lower():
            return 'Haarwäsche + Styling'
    
    return text

def get_service_description_translation(text, language):
    """Hizmet açıklamalarını çevir"""
    if not text:
        return text
    
    # Önce tam eşleşme ara
    if language in TRANSLATIONS and text in TRANSLATIONS[language]:
        return TRANSLATIONS[language][text]
    
    # Genel açıklama çevirileri
    if language == 'en':
        if 'geleneksel' in text.lower() and 'berber' in text.lower():
            return 'Clean and neat appearance with traditional barber cut. Includes washing, cutting and styling.'
        elif 'güncel' in text.lower() and 'trend' in text.lower():
            return 'Modern haircut according to current trends. Includes washing, cutting, styling and styling.'
        elif 'saç kesimi' in text.lower() and 'sakal bakımı' in text.lower() and 'masaj' in text.lower():
            return 'Haircut, beard care, facial care, massage. Full service package.'
        elif 'gri sakal' in text.lower() and 'boyama' in text.lower():
            return 'Service for coloring gray beards to natural color. Quality dyes are used.'
        elif 'profesyonel' in text.lower() and 'sakal kesimi' in text.lower():
            return 'Professional beard cutting and styling. Includes cleaning and care.'
        elif 'ekonomik paket' in text.lower() and 'saç' in text.lower() and 'sakal' in text.lower():
            return 'Economic package where haircut and beard care are done together. Includes washing and styling.'
        elif 'çocuk' in text.lower() and 'özel' in text.lower():
            return 'Special haircut service for children. Patient and fun approach.'
        elif 'yıkama' in text.lower() and 'şekillendirme' in text.lower() and 'kesim' not in text.lower():
            return 'Professional hair washing and styling. Care without cutting.'
    
    elif language == 'de':
        if 'geleneksel' in text.lower() and 'berber' in text.lower():
            return 'Sauberes und ordentliches Aussehen mit traditionellem Friseurschnitt. Waschen, Schneiden und Styling inbegriffen.'
        elif 'güncel' in text.lower() and 'trend' in text.lower():
            return 'Moderner Haarschnitt nach aktuellen Trends. Waschen, Schneiden, Styling und Styling inbegriffen.'
        elif 'saç kesimi' in text.lower() and 'sakal bakımı' in text.lower() and 'masaj' in text.lower():
            return 'Haarschnitt, Bartpflege, Gesichtspflege, Massage. Vollservice-Paket.'
        elif 'gri sakal' in text.lower() and 'boyama' in text.lower():
            return 'Service zum Färben grauer Bärte in natürliche Farbe. Hochwertige Farben werden verwendet.'
        elif 'profesyonel' in text.lower() and 'sakal kesimi' in text.lower():
            return 'Professionelles Bartschneiden und -styling. Reinigung und Pflege inbegriffen.'
        elif 'ekonomik paket' in text.lower() and 'saç' in text.lower() and 'sakal' in text.lower():
            return 'Wirtschaftliches Paket mit Haarschnitt und Bartpflege zusammen. Waschen und Styling inbegriffen.'
        elif 'çocuk' in text.lower() and 'özel' in text.lower():
            return 'Spezieller Haarschnittservice für Kinder. Geduldiger und unterhaltsamer Ansatz.'
        elif 'yıkama' in text.lower() and 'şekillendirme' in text.lower() and 'kesim' not in text.lower():
            return 'Professionelle Haarwäsche und Styling. Pflege ohne Schneiden.'
    
    return text


def ana_sayfa(request):
    """Ana sayfa view'ı"""
    berberler = Berber.objects.filter(aktif=True)
    hizmetler = Hizmet.objects.filter(aktif=True)
    galeri = Galeri.objects.filter(aktif=True).order_by('sira')[:6]  # İlk 6 fotoğraf
    
    # Site ayarlarını al
    try:
        site_ayarlari = SiteAyarlari.objects.first()
    except SiteAyarlari.DoesNotExist:
        site_ayarlari = None
    
    # Dil bilgisini al
    language = request.session.get('language', 'de')
    
    # Hizmetleri çeviri ile birlikte hazırla (veritabanı çevirisi öncelikli)
    hizmetler_with_translation = []
    for hizmet in hizmetler:
        translated = None
        if language in ('en', 'de'):
            translated = HizmetTranslation.objects.filter(hizmet=hizmet, language=language).first()
        hizmet_data = {
            'id': hizmet.id,
            'ad': (translated.ad if translated and translated.ad else get_translation(hizmet.ad, language)),
            'aciklama': (translated.aciklama if translated and translated.aciklama else (get_service_description_translation(hizmet.aciklama, language) if hizmet.aciklama else '')),
            'fiyat': hizmet.fiyat,
            'sure_dakika': hizmet.sure_dakika,
            'aktif': hizmet.aktif,
            'olusturma_tarihi': hizmet.olusturma_tarihi,
        }
        hizmetler_with_translation.append(hizmet_data)
    
    # Hizmetleri carousel için gruplara böl
    # Desktop için 3'lü gruplar
    hizmetler_grouped_desktop = []
    for i in range(0, len(hizmetler_with_translation), 3):
        hizmetler_grouped_desktop.append(hizmetler_with_translation[i:i+3])
    
    # Mobil için 1'li gruplar (her hizmet ayrı slide)
    hizmetler_grouped_mobile = [[hizmet] for hizmet in hizmetler_with_translation]
    
    context = {
        'berberler': berberler,
        'hizmetler': hizmetler_with_translation,
        'hizmetler_grouped_desktop': hizmetler_grouped_desktop,  # Desktop için 3'lü gruplar
        'hizmetler_grouped_mobile': hizmetler_grouped_mobile,    # Mobil için 1'li gruplar
        'galeri': galeri,
        'site_ayarlari': site_ayarlari,
        'language': language,
        'get_translation': lambda text: get_translation(text, language),
    }
    return render(request, 'berber/ana_sayfa.html', context)


def randevu_al(request):
    """Randevu alma sayfası"""
    berberler = Berber.objects.filter(aktif=True)
    hizmetler = Hizmet.objects.filter(aktif=True)
    
    language = request.session.get('language', 'de')

    if request.method == 'POST':
        form = RandevuForm(request.POST, language=language)
        if form.is_valid():
            # ManyToMany için commit=False kullan
            randevu = form.save(commit=False)
            randevu.save()  # Önce randevuyu kaydet
            
            # Seçili hizmetleri kaydet
            selected_hizmetler = form.cleaned_data['hizmetler']
            randevu.hizmetler.set(selected_hizmetler)
            
            # Randevu başarıyla kaydedildi
            print(f"✅ Randevu kaydedildi: {randevu.ad} {randevu.soyad} - {randevu.tarih} {randevu.saat}")
            
            # Hizmetler listesi ve toplam fiyat (Almanca çeviri ile)
            def get_hizmet_ad_translated(hizmet, lang='de'):
                """Hizmetin çevrilmiş adını döndürür"""
                try:
                    translation = hizmet.translations.get(language=lang)
                    return translation.ad if translation.ad else hizmet.ad
                except:
                    return hizmet.ad
            
            hizmetler_listesi = "\n".join([f"- {get_hizmet_ad_translated(h, 'de')} ({h.fiyat}€)" for h in selected_hizmetler])
            toplam_fiyat = sum(h.fiyat for h in selected_hizmetler)
            
            # Site sahibine bildirim oluştur ve mail gönder
            try:
                site_ayarlari = SiteAyarlari.objects.first()
                if site_ayarlari:
                    # İletişim tablosuna bildirim ekle
                    from .models import Iletisim
                    Iletisim.objects.create(
                        ad="Sistem",
                        soyad="Bildirimi",
                        email="sistem@berber.com",
                        telefon="000-000-0000",
                        konu=f"Yeni Randevu - {randevu.ad} {randevu.soyad}",
                        mesaj=f"""
YENİ RANDEVU BİLDİRİMİ

Müşteri: {randevu.ad} {randevu.soyad}
Telefon: {randevu.telefon}
E-posta: {randevu.email}
Berber: {randevu.berber.ad}

Hizmetler:
{hizmetler_listesi}

Toplam Fiyat: {toplam_fiyat}€
Tarih: {randevu.tarih}
Saat: {randevu.saat}
Notlar: {randevu.notlar or 'Yok'}

Bu randevu admin panelinde görüntülenebilir.
                        """,
                        okundu=False
                    )
                    print(f"📧 Site sahibine bildirim oluşturuldu!")
                    
                    # Yöneticiye mail gönder (dinamik SMTP ayarları ile)
                    send_email_with_site_settings(
                        subject=f'YENİ RANDEVU - {randevu.ad} {randevu.soyad}',
                        message=f'''
YENİ RANDEVU BİLDİRİMİ

Müşteri: {randevu.ad} {randevu.soyad}
Telefon: {randevu.telefon}
E-posta: {randevu.email}
Berber: {randevu.berber.ad}

Hizmetler:
{hizmetler_listesi}

Toplam Fiyat: {toplam_fiyat}€
Tarih: {randevu.tarih}
Saat: {randevu.saat}
Notlar: {randevu.notlar or 'Yok'}

Admin panelinden randevuyu görüntüleyebilirsiniz:
{request.build_absolute_uri('/admin/berber/randevu/')}
                        ''',
                        recipient_list=[site_ayarlari.mail_username]
                    )
                    
                    # Müşteriye onay maili gönder
                    try:
                        # Dile göre mail içeriği
                        if language == 'de':
                            customer_subject = f'Neue Terminbenachrichtigung - {site_ayarlari.site_adi}'
                            customer_message = f'''
Sehr geehrte(r) {randevu.ad} {randevu.soyad},

Vielen Dank für Ihre Terminbuchung bei {site_ayarlari.site_adi}!

TERMINDETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Datum: {randevu.tarih.strftime('%d.%m.%Y')}
🕐 Uhrzeit: {randevu.saat.strftime('%H:%M')} Uhr
👤 Friseur: {randevu.berber.ad}

🛠️ Gebuchte Dienstleistungen:
{hizmetler_listesi}

💰 Gesamtpreis: {toplam_fiyat}€

STATUS: Ausstehend (wird in Kürze bestätigt)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WICHTIGE HINWEISE:
• Bitte erscheinen Sie pünktlich zu Ihrem Termin
• Bei Verspätung von mehr als 15 Minuten kann der Termin verfallen
• Stornierungen bitte mindestens 24 Stunden im Voraus

Kontakt:
📧 E-Mail: {site_ayarlari.email}
📞 Telefon: {site_ayarlari.telefon}
📍 Adresse: {site_ayarlari.adres}
🗺️ Google Maps: https://www.google.com/maps/search/?api=1&query={site_ayarlari.adres.replace(' ', '+').replace('\n', ',+')}

Wir freuen uns auf Ihren Besuch!

Mit freundlichen Grüßen
{site_ayarlari.site_adi}
                            '''
                        elif language == 'en':
                            customer_subject = f'New Appointment Notification - {site_ayarlari.site_adi}'
                            customer_message = f'''
Dear {randevu.ad} {randevu.soyad},

Thank you for booking an appointment with {site_ayarlari.site_adi}!

APPOINTMENT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {randevu.tarih.strftime('%d.%m.%Y')}
🕐 Time: {randevu.saat.strftime('%H:%M')}
👤 Barber: {randevu.berber.ad}

🛠️ Booked Services:
{hizmetler_listesi}

💰 Total Price: {toplam_fiyat}€

STATUS: Pending (will be confirmed shortly)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT NOTES:
• Please arrive on time for your appointment
• Appointments may be forfeited if you are more than 15 minutes late
• Cancellations must be made at least 24 hours in advance

Contact:
📧 Email: {site_ayarlari.email}
📞 Phone: {site_ayarlari.telefon}
📍 Address: {site_ayarlari.adres}
🗺️ Google Maps: https://www.google.com/maps/search/?api=1&query={site_ayarlari.adres.replace(' ', '+').replace('\n', ',+')}

We look forward to seeing you!

Best regards
{site_ayarlari.site_adi}
                            '''
                        else:  # Turkish
                            customer_subject = f'Yeni Randevu Bildirimi - {site_ayarlari.site_adi}'
                            customer_message = f'''
Sayın {randevu.ad} {randevu.soyad},

{site_ayarlari.site_adi} için randevu oluşturduğunuz için teşekkür ederiz!

RANDEVU DETAYLARI:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Tarih: {randevu.tarih.strftime('%d.%m.%Y')}
🕐 Saat: {randevu.saat.strftime('%H:%M')}
👤 Berber: {randevu.berber.ad}

🛠️ Seçilen Hizmetler:
{hizmetler_listesi}

💰 Toplam Ücret: {toplam_fiyat}€

DURUM: Beklemede (kısa süre içinde onaylanacaktır)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ÖNEMLİ NOTLAR:
• Lütfen randevunuza zamanında gelin
• 15 dakikadan fazla gecikme durumunda randevu iptal edilebilir
• İptal işlemleri için lütfen en az 24 saat önceden bildirim yapın

İletişim:
📧 E-posta: {site_ayarlari.email}
📞 Telefon: {site_ayarlari.telefon}
📍 Adres: {site_ayarlari.adres}
🗺️ Google Maps: https://www.google.com/maps/search/?api=1&query={site_ayarlari.adres.replace(' ', '+').replace('\n', ',+')}

Sizi aramızda görmekten mutluluk duyacağız!

Saygılarımızla
{site_ayarlari.site_adi}
                            '''
                        
                        # Müşteriye mail gönder
                        send_email_with_site_settings(
                            subject=customer_subject,
                            message=customer_message,
                            recipient_list=[randevu.email]
                        )
                        print(f"📧 Müşteriye onay maili gönderildi: {randevu.email}")
                        
                    except Exception as mail_error:
                        print(f"Müşteri mail gönderim hatası: {mail_error}")
                        # Müşteriye mail gitmese bile randevu alındı
                    
            except Exception as e:
                print(f"Bildirim oluşturma hatası: {e}")
            
            # Başarı mesajını dile göre çevir
            success_message = get_translation('Randevunuz başarıyla alındı! Size e-posta ile bilgi verilecektir.', language)
            messages.success(request, success_message)
            return redirect('randevu_al')
    else:
        form = RandevuForm(language=language)
    
    # Hizmetleri çeviri ile birlikte hazırla (veritabanı çevirisi öncelikli)
    hizmetler_with_translation = []
    for hizmet in hizmetler:
        translated = None
        if language in ('en', 'de'):
            translated = HizmetTranslation.objects.filter(hizmet=hizmet, language=language).first()
        hizmet_data = {
            'id': hizmet.id,
            'ad': (translated.ad if translated and translated.ad else get_translation(hizmet.ad, language)),
            'aciklama': (translated.aciklama if translated and translated.aciklama else (get_service_description_translation(hizmet.aciklama, language) if hizmet.aciklama else '')),
            'fiyat': hizmet.fiyat,
            'sure_dakika': hizmet.sure_dakika,
        }
        hizmetler_with_translation.append(hizmet_data)
    
    # JSON için de aynı çevirileri kullan
    hizmetler_json = []
    for hizmet_data in hizmetler_with_translation:
        hizmetler_json.append({
            'id': hizmet_data['id'],
            'ad': hizmet_data['ad'],
            'fiyat': float(hizmet_data['fiyat']),
            'sure': hizmet_data['sure_dakika']
        })
    
    context = {
        'form': form,
        'berberler': berberler,
        'hizmetler': hizmetler_with_translation,  # Çevirili hizmetler
        'hizmetler_json': hizmetler_json,
        'language': language,
    }
    return render(request, 'berber/randevu_al.html', context)


def fiyat_listesi(request):
    """Fiyat listesi sayfası"""
    hizmetler = Hizmet.objects.filter(aktif=True).order_by('sira', 'ad')
    language = request.session.get('language', 'de')
    
    # Hizmetleri çeviri ile birlikte hazırla (veritabanı çevirisi öncelikli)
    hizmetler_with_translation = []
    for hizmet in hizmetler:
        translated = None
        if language in ('en', 'de'):
            translated = HizmetTranslation.objects.filter(hizmet=hizmet, language=language).first()
        hizmet_data = {
            'id': hizmet.id,
            'ad': (translated.ad if translated and translated.ad else get_translation(hizmet.ad, language)),
            'aciklama': (translated.aciklama if translated and translated.aciklama else (get_service_description_translation(hizmet.aciklama, language) if hizmet.aciklama else '')),
            'fiyat': hizmet.fiyat,
            'sure_dakika': hizmet.sure_dakika,
            'aktif': hizmet.aktif,
            'olusturma_tarihi': hizmet.olusturma_tarihi,
        }
        hizmetler_with_translation.append(hizmet_data)
    
    context = {
        'hizmetler': hizmetler_with_translation,
        'language': language,
        'get_translation': lambda text: get_translation(text, language),
    }
    return render(request, 'berber/fiyat_listesi.html', context)


def galeri(request):
    """Galeri sayfası"""
    galeri_fotolari = Galeri.objects.filter(aktif=True).order_by('sira', '-olusturma_tarihi')
    
    context = {
        'galeri_fotolari': galeri_fotolari,
        'language': request.session.get('language', 'de'),
    }
    return render(request, 'berber/galeri.html', context)


def iletisim(request):
    """İletişim sayfası"""
    language = request.session.get('language', 'de')
    if request.method == 'POST':
        form = IletisimForm(request.POST, language=language)
        if form.is_valid():
            iletisim_mesaji = form.save()
            
            # Mesaj başarıyla kaydedildi
            print(f"✅ İletişim mesajı kaydedildi: {iletisim_mesaji.ad} {iletisim_mesaji.soyad} - {iletisim_mesaji.konu}")
            
            # Yöneticiye mail gönder (dinamik SMTP ayarları ile)
            try:
                site_ayarlari = SiteAyarlari.objects.first()
                if site_ayarlari:
                    send_email_with_site_settings(
                        subject=f'YENİ İLETİŞİM MESAJI - {iletisim_mesaji.konu}',
                        message=f'''
YENİ İLETİŞİM MESAJI

Gönderen: {iletisim_mesaji.ad} {iletisim_mesaji.soyad}
E-posta: {iletisim_mesaji.email}
Telefon: {iletisim_mesaji.telefon}
Konu: {iletisim_mesaji.konu}

Mesaj:
{iletisim_mesaji.mesaj}

Tarih: {iletisim_mesaji.olusturma_tarihi}

Admin panelinden mesajı görüntüleyebilirsiniz:
{request.build_absolute_uri('/admin/berber/iletisim/')}
                        ''',
                        recipient_list=[site_ayarlari.mail_username]
                    )
                    
            except Exception as e:
                print(f"Mail gönderim hatası: {e}")
            
            # Başarı mesajını dile göre çevir
            success_message = get_translation('Mesajınız başarıyla gönderildi! En kısa sürede size dönüş yapacağız.', language)
            messages.success(request, success_message)
            return redirect('iletisim')
    else:
        form = IletisimForm(language=language)
    
    # Site ayarlarını al
    try:
        site_ayarlari = SiteAyarlari.objects.first()
    except SiteAyarlari.DoesNotExist:
        site_ayarlari = None
    
    context = {
        'form': form,
        'site_ayarlari': site_ayarlari,
        'language': language,
    }
    return render(request, 'berber/iletisim.html', context)


def hizmet_detay(request, hizmet_id):
    """Hizmet detay sayfası"""
    hizmet = get_object_or_404(Hizmet, id=hizmet_id, aktif=True)
    
    context = {
        'hizmet': hizmet,
        'language': request.session.get('language', 'de'),
    }
    return render(request, 'berber/hizmet_detay.html', context)


def berber_detay(request, berber_id):
    """Berber detay sayfası"""
    berber = get_object_or_404(Berber, id=berber_id, aktif=True)
    
    context = {
        'berber': berber,
        'language': request.session.get('language', 'de'),
    }
    return render(request, 'berber/berber_detay.html', context)


@csrf_exempt
def ajax_randevu_kontrol(request):
    """AJAX ile randevu kontrolü"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tarih = data.get('tarih')
            berber_id = data.get('berber_id')
            
            if not tarih or not berber_id:
                return JsonResponse({'error': 'Tarih ve berber seçimi gerekli'}, status=400)
            
            # Seçilen tarihteki randevuları al
            randevular = Randevu.objects.filter(
                tarih=tarih,
                berber_id=berber_id,
                durum__in=['beklemede', 'onaylandi']
            )
            
            # Saatleri "HH:MM" formatına çevir
            dolu_saatler = []
            for randevu in randevular:
                saat_str = randevu.saat.strftime('%H:%M') if hasattr(randevu.saat, 'strftime') else str(randevu.saat)
                dolu_saatler.append(saat_str)
            
            # Mevcut saatleri döndür
            return JsonResponse({
                'dolu_saatler': dolu_saatler
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Geçersiz istek'}, status=400)


# ==================== BERBER PANELİ ====================

def berber_login(request):
    """Berber giriş sayfası"""
    # Zaten giriş yapmışsa panele yönlendir
    if request.user.is_authenticated:
        return redirect('berber_panel')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Başarıyla giriş yaptınız!')
            return redirect('berber_panel')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı!')
    
    return render(request, 'berber/panel_login.html')


@login_required(login_url='berber_login')
def berber_panel(request):
    """Berber yönetim paneli - Randevuları listeler"""
    
    # Arama ve filtreleme
    search_query = request.GET.get('search', '')
    durum_filter = request.GET.get('durum', '')
    tarih_filter = request.GET.get('tarih', '')
    berber_filter = request.GET.get('berber', '')
    
    # Tüm randevuları getir (en son oluşturulanlar en üstte)
    randevular = Randevu.objects.all().select_related('berber').prefetch_related('hizmetler').order_by('-id')
    
    # Arama
    if search_query:
        randevular = randevular.filter(
            Q(ad__icontains=search_query) |
            Q(soyad__icontains=search_query) |
            Q(telefon__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Durum filtresi
    if durum_filter:
        randevular = randevular.filter(durum=durum_filter)
    
    # Tarih filtresi
    if tarih_filter:
        randevular = randevular.filter(tarih=tarih_filter)
    
    # Berber filtresi
    if berber_filter:
        randevular = randevular.filter(berber_id=berber_filter)
    
    # İstatistikler
    bugun = date.today()
    istatistikler = {
        'toplam': Randevu.objects.count(),
        'beklemede': Randevu.objects.filter(durum='beklemede').count(),
        'onaylandi': Randevu.objects.filter(durum='onaylandi').count(),
        'bugun': Randevu.objects.filter(tarih=bugun).count(),
    }
    
    # Aktif berberleri al
    berberler = Berber.objects.filter(aktif=True).order_by('ad')
    
    context = {
        'randevular': randevular,
        'istatistikler': istatistikler,
        'search_query': search_query,
        'durum_filter': durum_filter,
        'tarih_filter': tarih_filter,
        'berber_filter': berber_filter,
        'durum_choices': Randevu.DURUM_CHOICES,
        'berberler': berberler,
    }
    
    return render(request, 'berber/berber_panel.html', context)


@login_required(login_url='berber_login')
def berber_logout(request):
    """Berber çıkış"""
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptınız!')
    return redirect('ana_sayfa')


@login_required(login_url='berber_login')
def randevu_durum_guncelle(request, randevu_id):
    """Randevu durumunu güncelle (AJAX)"""
    if request.method == 'POST':
        try:
            randevu = get_object_or_404(Randevu, id=randevu_id)
            data = json.loads(request.body)
            yeni_durum = data.get('durum')
            
            if yeni_durum in ['beklemede', 'onaylandi', 'tamamlandi', 'iptal']:
                eski_durum = randevu.durum
                randevu.durum = yeni_durum
                randevu.save()
                
                # Durum değişikliğinde müşteriye bildirim maili gönder
                if eski_durum != yeni_durum and yeni_durum != 'beklemede':
                    try:
                        site_ayarlari = SiteAyarlari.objects.first()
                        
                        # Hizmetler listesi (Almanca çeviri ile)
                        def get_hizmet_ad_translated(hizmet, lang='de'):
                            """Hizmetin çevrilmiş adını döndürür"""
                            try:
                                translation = hizmet.translations.get(language=lang)
                                return translation.ad if translation.ad else hizmet.ad
                            except:
                                return hizmet.ad
                        
                        hizmetler = randevu.hizmetler.all()
                        hizmetler_listesi = '\n'.join([f"- {get_hizmet_ad_translated(h, 'de')} ({h.fiyat}€)" for h in hizmetler])
                        
                        # Durum mesajları
                        durum_mesajlari = {
                            'onaylandi': {
                                'tr': ('Randevunuz Onaylandı! ✅', 'Randevunuz onaylanmıştır. Belirlenen tarih ve saatte bekliyoruz.'),
                                'de': ('Ihr Termin wurde bestätigt! ✅', 'Ihr Termin wurde bestätigt. Wir erwarten Sie zum vereinbarten Datum und zur vereinbarten Uhrzeit.'),
                                'en': ('Your Appointment Confirmed! ✅', 'Your appointment has been confirmed. We look forward to seeing you at the scheduled date and time.')
                            },
                            'tamamlandi': {
                                'tr': ('Randevunuz Tamamlandı ✨', 'Randevunuz başarıyla tamamlanmıştır. Bizi tercih ettiğiniz için teşekkür ederiz!'),
                                'de': ('Ihr Termin wurde abgeschlossen ✨', 'Ihr Termin wurde erfolgreich abgeschlossen. Vielen Dank, dass Sie uns gewählt haben!'),
                                'en': ('Your Appointment Completed ✨', 'Your appointment has been successfully completed. Thank you for choosing us!')
                            },
                            'iptal': {
                                'tr': ('Randevunuz İptal Edildi ❌', 'Randevunuz iptal edilmiştir. Yeni randevu almak için websitemizi ziyaret edebilirsiniz.'),
                                'de': ('Ihr Termin wurde storniert ❌', 'Ihr Termin wurde storniert. Sie können unsere Website besuchen, um einen neuen Termin zu vereinbaren.'),
                                'en': ('Your Appointment Cancelled ❌', 'Your appointment has been cancelled. You can visit our website to book a new appointment.')
                            }
                        }
                        
                        # Durum çevirileri
                        durum_cevirileri = {
                            'beklemede': {
                                'tr': 'Beklemede',
                                'de': 'Ausstehend',
                                'en': 'Pending'
                            },
                            'onaylandi': {
                                'tr': 'Onaylandı',
                                'de': 'Bestätigt',
                                'en': 'Confirmed'
                            },
                            'tamamlandi': {
                                'tr': 'Tamamlandı',
                                'de': 'Abgeschlossen',
                                'en': 'Completed'
                            },
                            'iptal': {
                                'tr': 'İptal',
                                'de': 'Storniert',
                                'en': 'Cancelled'
                            }
                        }
                        
                        # Dil belirleme - Tüm durum güncellemeleri Almanca
                        language = 'de'
                        
                        durum_basligi, durum_mesaji = durum_mesajlari[yeni_durum][language]
                        durum_text = durum_cevirileri[yeni_durum][language]
                        
                        # Mail içeriği
                        if language == 'de':
                            subject = f'{durum_basligi} - {site_ayarlari.site_adi}'
                            message = f'''
Sehr geehrte(r) {randevu.ad} {randevu.soyad},

{durum_mesaji}

TERMINDETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Datum: {randevu.tarih.strftime('%d.%m.%Y')}
🕐 Uhrzeit: {randevu.saat.strftime('%H:%M')} Uhr
👤 Friseur: {randevu.berber.ad}

🛠️ Dienstleistungen:
{hizmetler_listesi}

💰 Gesamtpreis: {randevu.toplam_fiyat}€

STATUS: {durum_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Kontakt:
📧 E-Mail: {site_ayarlari.email}
📞 Telefon: {site_ayarlari.telefon}
📍 Adresse: {site_ayarlari.adres}
🗺️ Google Maps: https://www.google.com/maps/search/?api=1&query={site_ayarlari.adres.replace(' ', '+').replace('\n', ',+')}

Mit freundlichen Grüßen
{site_ayarlari.site_adi}
                            '''
                        elif language == 'en':
                            subject = f'{durum_basligi} - {site_ayarlari.site_adi}'
                            message = f'''
Dear {randevu.ad} {randevu.soyad},

{durum_mesaji}

APPOINTMENT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {randevu.tarih.strftime('%d.%m.%Y')}
🕐 Time: {randevu.saat.strftime('%H:%M')}
👤 Barber: {randevu.berber.ad}

🛠️ Services:
{hizmetler_listesi}

💰 Total Price: {randevu.toplam_fiyat}€

STATUS: {durum_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Contact:
📧 Email: {site_ayarlari.email}
📞 Phone: {site_ayarlari.telefon}
📍 Address: {site_ayarlari.adres}
🗺️ Google Maps: https://www.google.com/maps/search/?api=1&query={site_ayarlari.adres.replace(' ', '+').replace('\n', ',+')}

Best regards
{site_ayarlari.site_adi}
                            '''
                        else:  # Turkish
                            subject = f'{durum_basligi} - {site_ayarlari.site_adi}'
                            message = f'''
Sayın {randevu.ad} {randevu.soyad},

{durum_mesaji}

RANDEVU DETAYLARI:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Tarih: {randevu.tarih.strftime('%d.%m.%Y')}
🕐 Saat: {randevu.saat.strftime('%H:%M')}
👤 Berber: {randevu.berber.ad}

🛠️ Hizmetler:
{hizmetler_listesi}

💰 Toplam Ücret: {randevu.toplam_fiyat}€

DURUM: {durum_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

İletişim:
📧 E-posta: {site_ayarlari.email}
📞 Telefon: {site_ayarlari.telefon}
📍 Adres: {site_ayarlari.adres}
🗺️ Google Maps: https://www.google.com/maps/search/?api=1&query={site_ayarlari.adres.replace(' ', '+').replace('\n', ',+')}

Saygılarımızla
{site_ayarlari.site_adi}
                            '''
                        
                        # Mail gönder
                        send_email_with_site_settings(
                            subject=subject,
                            message=message,
                            recipient_list=[randevu.email]
                        )
                        
                        print(f"✅ Durum değişikliği maili gönderildi: {randevu.email} - {yeni_durum}")
                        
                    except Exception as mail_error:
                        print(f"⚠️ Mail gönderim hatası: {mail_error}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Durum güncellendi ve müşteriye bildirim gönderildi'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Geçersiz durum'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek'}, status=400)


@login_required(login_url='berber_login')
def panel_check_new_appointments(request):
    """Panel için yeni randevu kontrolü (AJAX)"""
    if request.method == 'GET':
        try:
            # Toplam randevu sayısını döndür
            total_count = Randevu.objects.count()
            beklemede_count = Randevu.objects.filter(durum='beklemede').count()
            
            return JsonResponse({
                'total_count': total_count,
                'beklemede_count': beklemede_count,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Geçersiz istek'}, status=400)


@login_required(login_url='berber_login')
def customer_history(request):
    """Müşteri geçmişini getir (AJAX)"""
    if request.method == 'GET':
        try:
            email = request.GET.get('email', '')
            telefon = request.GET.get('telefon', '')
            
            if not email and not telefon:
                return JsonResponse({
                    'success': False,
                    'message': 'Email veya telefon gerekli'
                }, status=400)
            
            # Aynı email veya telefona sahip tüm randevuları getir
            from django.db.models import Q
            
            query = Q()
            if email:
                query |= Q(email=email)
            if telefon:
                query |= Q(telefon=telefon)
            
            randevular = Randevu.objects.filter(query).select_related('berber').prefetch_related('hizmetler').order_by('-tarih', '-saat')
            
            # Müşteri bilgileri (ilk randevudan)
            first_randevu = randevular.first()
            if not first_randevu:
                return JsonResponse({
                    'success': True,
                    'customer': {
                        'name': 'Bilinmeyen Müşteri',
                        'email': email,
                        'phone': telefon
                    },
                    'history': []
                })
            
            customer_data = {
                'name': f"{first_randevu.ad} {first_randevu.soyad}",
                'email': first_randevu.email,
                'phone': first_randevu.telefon
            }
            
            # Randevu geçmişini hazırla
            history_data = []
            for randevu in randevular:
                # Hizmetleri al
                hizmetler = [h.ad for h in randevu.hizmetler.all()]
                
                history_data.append({
                    'date': randevu.tarih.strftime('%d.%m.%Y'),
                    'time': randevu.saat.strftime('%H:%M'),
                    'barber': randevu.berber.ad,
                    'services': hizmetler,
                    'total_price': float(randevu.toplam_fiyat),
                    'status': randevu.durum,
                    'notes': randevu.notlar or ''
                })
            
            return JsonResponse({
                'success': True,
                'customer': customer_data,
                'history': history_data
            })
            
        except Exception as e:
            print(f"Müşteri geçmişi hatası: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek'}, status=400)
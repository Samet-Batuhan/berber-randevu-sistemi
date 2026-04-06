from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time, datetime
from .models import Randevu, Iletisim, Berber, Hizmet


class RandevuForm(forms.ModelForm):
    """Randevu formu"""
    
    # Çoklu hizmet seçimi için özel alan
    hizmetler = forms.ModelMultipleChoiceField(
        queryset=Hizmet.objects.filter(aktif=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label='Hizmetler'
    )
    
    class Meta:
        model = Randevu
        fields = ['ad', 'soyad', 'telefon', 'email', 'berber', 'hizmetler', 'tarih', 'saat', 'notlar']
        widgets = {
            'ad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adınız'
            }),
            'soyad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Soyadınız'
            }),
            'telefon': forms.TextInput(attrs={
                'class': 'form-control phone-input',
                'type': 'tel',
                'placeholder': '+49 123 4567890'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-posta adresiniz'
            }),
            'berber': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tarih': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d')
            }),
            'saat': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'notlar': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ek notlarınız (opsiyonel)'
            }),
        }
        labels = {
            'ad': 'Ad',
            'soyad': 'Soyad',
            'telefon': 'Telefon',
            'email': 'E-posta',
            'berber': 'Berber',
            'hizmetler': 'Hizmetler',
            'tarih': 'Tarih',
            'saat': 'Saat',
            'notlar': 'Notlar',
        }

    def __init__(self, *args, **kwargs):
        language = kwargs.pop('language', 'tr')
        super().__init__(*args, **kwargs)
        # Sadece aktif berberleri ve hizmetleri göster
        self.fields['berber'].queryset = Berber.objects.filter(aktif=True)
        self.fields['hizmetler'].queryset = Hizmet.objects.filter(aktif=True)

        # Etiket ve placeholder çevirileri
        try:
            # Döngü importunu önlemek için burada import
            from .views import TRANSLATIONS
        except Exception:
            TRANSLATIONS = {}

        def tr(text: str) -> str:
            if language in TRANSLATIONS and text in TRANSLATIONS[language]:
                return TRANSLATIONS[language][text]
            return text

        # Labels
        for field_name in self.fields:
            if self.fields[field_name].label:
                self.fields[field_name].label = tr(self.fields[field_name].label)

        # Placeholders
        placeholders = {
            'ad': 'Adınız',
            'soyad': 'Soyadınız',
            'telefon': 'Telefon numaranız',
            'email': 'E-posta adresiniz',
            'notlar': 'Ek notlarınız (opsiyonel)',
        }
        for name, text in placeholders.items():
            if name in self.fields and 'placeholder' in self.fields[name].widget.attrs:
                self.fields[name].widget.attrs['placeholder'] = tr(text)

    def clean_tarih(self):
        """Tarih validasyonu"""
        tarih = self.cleaned_data.get('tarih')
        if tarih:
            if tarih < date.today():
                raise ValidationError('Geçmiş tarih seçemezsiniz.')
            
            # Salı (1) ve Pazar (6) kapalı
            if tarih.weekday() in [1, 6]:
                raise ValidationError('Seçtiğiniz gün kapalıdır.')
        return tarih

    def clean_saat(self):
        """Saat validasyonu - Güne göre değişken çalışma saatleri"""
        saat = self.cleaned_data.get('saat')
        if saat:
            # 30 dakikalık aralıklarla kontrol et
            if saat.minute not in [0, 30]:
                raise ValidationError('Randevu saatleri sadece 30 dakikalık aralıklarla alınabilir (örn: 09:00, 09:30, 10:00)')
        return saat

    def clean(self):
        """Form genel validasyonu"""
        cleaned_data = super().clean()
        tarih = cleaned_data.get('tarih')
        saat = cleaned_data.get('saat')
        berber = cleaned_data.get('berber')
        
        # Güne göre çalışma saatleri kontrolü
        if tarih and saat:
            weekday = tarih.weekday()
            
            # Çalışma saatleri tanımları
            # Pazartesi (0), Çarşamba (2), Perşembe (3), Cuma (4): 09:00-19:00
            # Cumartesi (5): 09:00-16:00
            # Salı (1), Pazar (6): Kapalı (zaten clean_tarih'te kontrol ediliyor)
            
            if weekday == 5:  # Cumartesi
                if saat < time(9, 0) or saat >= time(16, 0):
                    raise ValidationError('Cumartesi çalışma saatleri: 09:00 - 16:00')
            elif weekday in [0, 2, 3, 4]:  # Pazartesi, Çarşamba, Perşembe, Cuma
                if saat < time(9, 0) or saat >= time(19, 0):
                    raise ValidationError('Çalışma saatleri: 09:00 - 19:00')
        
        if tarih and saat and berber:
            # Aynı tarih ve saatte başka randevu var mı kontrol et
            mevcut_randevu = Randevu.objects.filter(
                tarih=tarih,
                saat=saat,
                berber=berber,
                durum__in=['beklemede', 'onaylandi']
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if mevcut_randevu.exists():
                raise ValidationError('Bu saatte zaten bir randevu bulunmaktadır.')
        
        return cleaned_data


class IletisimForm(forms.ModelForm):
    """İletişim formu"""
    
    class Meta:
        model = Iletisim
        fields = ['ad', 'soyad', 'telefon', 'email', 'konu', 'mesaj']
        widgets = {
            'ad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adınız'
            }),
            'soyad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Soyadınız'
            }),
            'telefon': forms.TextInput(attrs={
                'class': 'form-control phone-input',
                'type': 'tel',
                'placeholder': '+49 123 4567890'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-posta adresiniz'
            }),
            'konu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mesaj konusu'
            }),
            'mesaj': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Mesajınız'
            }),
        }
        labels = {
            'ad': 'Ad',
            'soyad': 'Soyad',
            'telefon': 'Telefon',
            'email': 'E-posta',
            'konu': 'Konu',
            'mesaj': 'Mesaj',
        }

    def __init__(self, *args, **kwargs):
        language = kwargs.pop('language', 'tr')
        super().__init__(*args, **kwargs)

        try:
            from .views import TRANSLATIONS
        except Exception:
            TRANSLATIONS = {}

        def tr(text: str) -> str:
            if language in TRANSLATIONS and text in TRANSLATIONS[language]:
                return TRANSLATIONS[language][text]
            return text

        # Labels
        for field_name in self.fields:
            if self.fields[field_name].label:
                self.fields[field_name].label = tr(self.fields[field_name].label)

        # Placeholders
        placeholders = {
            'ad': 'Adınız',
            'soyad': 'Soyadınız',
            'telefon': 'Telefon numaranız',
            'email': 'E-posta adresiniz',
            'konu': 'Mesaj konusu',
            'mesaj': 'Mesajınız',
        }
        for name, text in placeholders.items():
            if name in self.fields and 'placeholder' in self.fields[name].widget.attrs:
                self.fields[name].widget.attrs['placeholder'] = tr(text)

    def clean_telefon(self):
        """Telefon numarası validasyonu - Uluslararası format desteği"""
        telefon = self.cleaned_data.get('telefon')
        if telefon:
            # Tüm boşlukları, tireleri ve parantezleri temizle
            cleaned = telefon.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            # + işareti sadece başta olabilir
            if '+' in cleaned[1:]:
                raise ValidationError('Geçersiz telefon formatı.')
            
            # Sadece rakam ve başta + işareti kabul et
            if not cleaned.replace('+', '').isdigit():
                raise ValidationError('Telefon numarası sadece rakam ve + işareti içerebilir.')
            
            # Minimum uzunluk kontrolü (ülke kodu dahil)
            if len(cleaned.replace('+', '')) < 10:
                raise ValidationError('Telefon numarası çok kısa. En az 10 rakam olmalı.')
            
            # Maksimum uzunluk kontrolü
            if len(cleaned.replace('+', '')) > 15:
                raise ValidationError('Telefon numarası çok uzun.')
                
        return telefon

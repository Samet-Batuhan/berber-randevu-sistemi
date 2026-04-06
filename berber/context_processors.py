from .models import SiteAyarlari


def language(request):
    """Tüm template'lere dil bilgisini ve site ayarlarını ilet.

    Not: Site ayarlarını zaten base'de kullanıyoruz; burada hazır dursun.
    """
    lang = request.session.get('language', 'de')  # Varsayılan dil Almanca
    try:
        site_ayarlari = SiteAyarlari.objects.first()
    except Exception:
        site_ayarlari = None

    return {
        'language': lang,
        'site_ayarlari': site_ayarlari,
    }



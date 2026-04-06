from django.urls import path
from . import views

urlpatterns = [
    path('', views.ana_sayfa, name='ana_sayfa'),
    path('randevu-al/', views.randevu_al, name='randevu_al'),
    path('fiyat-listesi/', views.fiyat_listesi, name='fiyat_listesi'),
    path('galeri/', views.galeri, name='galeri'),
    path('iletisim/', views.iletisim, name='iletisim'),
    path('hizmet/<int:hizmet_id>/', views.hizmet_detay, name='hizmet_detay'),
    path('berber/<int:berber_id>/', views.berber_detay, name='berber_detay'),
    path('ajax/randevu-kontrol/', views.ajax_randevu_kontrol, name='ajax_randevu_kontrol'),
    path('set-language/', views.set_language, name='set_language'),
    
    # Berber Paneli
    path('berber-giris/', views.berber_login, name='berber_login'),
    path('berber-panel/', views.berber_panel, name='berber_panel'),
    path('berber-cikis/', views.berber_logout, name='berber_logout'),
    path('randevu-durum/<int:randevu_id>/', views.randevu_durum_guncelle, name='randevu_durum_guncelle'),
    path('panel-check-new/', views.panel_check_new_appointments, name='panel_check_new_appointments'),
    path('musteri-gecmisi/', views.customer_history, name='customer_history'),
]

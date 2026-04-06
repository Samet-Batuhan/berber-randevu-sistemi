from django import template
from berber.views import get_translation
import re

register = template.Library()

@register.filter
def to_whatsapp(phone_number):
    """Telefon numarasını WhatsApp linkine çevir"""
    if not phone_number:
        return '#'
    
    # Telefon numarasından sadece rakamları al
    clean_number = re.sub(r'[^\d+]', '', str(phone_number))
    
    # + işaretini kaldır
    clean_number = clean_number.replace('+', '')
    
    # WhatsApp linkini oluştur
    return f'https://wa.me/{clean_number}'

@register.simple_tag
def trans(text, language='tr'):
    """Çeviri template tag'i"""
    return get_translation(text, language)

@register.simple_tag
def trans_multiline(text, language='tr'):
    """Çok satırlı metinler için satır satır çeviri - gün isimleri ve aralıkları"""
    if not text:
        return text
    
    # Her satırı ayrı ayrı işle
    lines = text.split('\n')
    translated_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            translated_lines.append('')
            continue
        
        # Satırı ':' karakterinden böl
        if ':' in line:
            parts = line.split(':', 1)  # Sadece ilk : karakterinden böl
            day_part = parts[0].strip()  # Gün ismi/aralığı kısmı
            time_part = parts[1].strip() if len(parts) > 1 else ''  # Saat kısmı
            
            # Gün aralığı mı kontrol et (örn: "Çarşamba - Cuma")
            if ' - ' in day_part:
                day_range_parts = day_part.split(' - ')
                translated_days = []
                for day in day_range_parts:
                    translated_days.append(get_translation(day.strip(), language))
                
                # Dil bazlı formatla
                if language == 'de':
                    translated_day = '–'.join(translated_days)  # Almanca: uzun tire
                elif language == 'en':
                    translated_day = ' - '.join(translated_days)  # İngilizce: kısa tire boşluklu
                else:
                    translated_day = ' - '.join(translated_days)  # Türkçe: kısa tire boşluklu
            else:
                # Tek gün
                translated_day = get_translation(day_part, language)
            
            # Saat kısmını işle
            if time_part:
                # "Kapalı" mı kontrol et
                if 'Kapalı' in time_part or 'kapalı' in time_part.lower():
                    translated_time = get_translation('Kapalı', language)
                    if language == 'de':
                        translated_lines.append(f"{translated_day}: {translated_time}")
                    elif language == 'en':
                        translated_lines.append(f"{translated_day}: {translated_time}")
                    else:
                        translated_lines.append(f"{translated_day} : {translated_time}")
                else:
                    # Saat aralığını formatla
                    if language == 'de':
                        # Almanca: "9:00–19:00 Uhr" formatı
                        # Tüm başındaki 0'ları kaldır (09:00, 08:00 vs.)
                        formatted_time = re.sub(r'\b0(\d):', r'\1:', time_part)
                        # Tire işaretlerini uzun tire ile değiştir
                        formatted_time = formatted_time.replace(' - ', '–')
                        if 'Uhr' not in formatted_time:
                            formatted_time += ' Uhr'
                        translated_lines.append(f"{translated_day}: {formatted_time}")
                    elif language == 'en':
                        # İngilizce: "9:00 - 19:00" formatı
                        formatted_time = re.sub(r'\b0(\d):', r'\1:', time_part)
                        translated_lines.append(f"{translated_day}: {formatted_time}")
                    else:
                        # Türkçe: orijinal format
                        translated_lines.append(f"{translated_day} : {time_part}")
            else:
                translated_lines.append(translated_day)
        else:
            # ':' yoksa tüm satırı çevir
            translated_lines.append(get_translation(line, language))
    
    return '\n'.join(translated_lines)
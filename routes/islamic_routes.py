from flask import Blueprint, render_template, request, jsonify, Response, current_app
from routes.shared import get_lang
import math
import datetime
import io
import csv
import calendar as cal_module
import traceback
import os
import json
try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

from database.quran_surahs import SURAHS, RECITERS

islamic_bp = Blueprint('islamic', __name__)

DEFAULT_LAT = 8.9806
DEFAULT_LNG = 38.7578
KAABA_LAT   = 21.4225
KAABA_LNG   = 39.8262

HIJRI_MONTHS = [
    'Muharram', 'Safar', 'Rabi al-Awwal', 'Rabi al-Thani',
    'Jumada al-Awwal', 'Jumada al-Thani', 'Rajab', "Sha'ban",
    'Ramadan', 'Shawwal', "Dhul Qi'dah", 'Dhul Hijjah'
]

ISLAMIC_HOLIDAYS = [
    (1,  1,  'Islamic New Year',    '🌙'),
    (1,  10, 'Day of Ashura',       '🤲'),
    (3,  12, 'Mawlid al-Nabi',      '⭐'),
    (7,  27, "Isra and Mi'raj",     '🌃'),
    (8,  15, "Laylat al-Bara'ah",   '🌕'),
    (9,  1,  'Start of Ramadan',    '🌙'),
    (9,  27, 'Laylat al-Qadr',      '✨'),
    (10, 1,  'Eid al-Fitr',         '🎉'),
    (12, 9,  'Day of Arafah',       '🕋'),
    (12, 10, 'Eid al-Adha',         '🐑'),
]

ADDIS_FALLBACK = {
    'Fajr': '04:45', 'Dhuhr': '12:20', 'Asr': '15:35',
    'Maghrib': '18:35', 'Isha': '19:50'
}

ETHIOPIAN_CITIES = [
    {'name': 'ወሎ ደሴ ኩታበር',        'lat': 8.9806,  'lng': 38.7578},
    {'name': 'Adama (Nazret)',      'lat': 8.5400,  'lng': 39.2700},
    {'name': 'Arba Minch',         'lat': 6.0333,  'lng': 37.5500},
    {'name': 'Assosa',             'lat': 10.0667, 'lng': 34.5333},
    {'name': 'Asebe Teferi',       'lat': 9.0700,  'lng': 40.8700},
    {'name': 'Awash',              'lat': 8.9922,  'lng': 40.1658},
    {'name': 'Axum',               'lat': 14.1206, 'lng': 38.7197},
    {'name': 'Bahir Dar',          'lat': 11.5742, 'lng': 37.3614},
    {'name': 'Bishoftu (Debre Zeit)', 'lat': 8.7500, 'lng': 38.9833},
    {'name': 'Bonga',              'lat': 7.2667,  'lng': 36.2333},
    {'name': 'Debre Birhan',       'lat': 9.6833,  'lng': 39.5333},
    {'name': 'Debre Markos',       'lat': 10.3500, 'lng': 37.7333},
    {'name': 'Dessie',             'lat': 11.1333, 'lng': 39.6333},
    {'name': 'Dilla',              'lat': 6.4167,  'lng': 38.3167},
    {'name': 'Dire Dawa',          'lat': 9.5931,  'lng': 41.8661},
    {'name': 'Gambela',            'lat': 8.2500,  'lng': 34.5833},
    {'name': 'Gondar',             'lat': 12.6033, 'lng': 37.4521},
    {'name': 'Harar',              'lat': 9.3111,  'lng': 42.1236},
    {'name': 'Hawassa',            'lat': 7.0620,  'lng': 38.4769},
    {'name': 'Jijiga',             'lat': 9.3500,  'lng': 42.7833},
    {'name': 'Jimma',              'lat': 7.6780,  'lng': 36.8340},
    {'name': 'Lalibela',           'lat': 12.0317, 'lng': 39.0450},
    {'name': 'Mekelle',            'lat': 13.4967, 'lng': 39.4767},
    {'name': 'Nekemte',            'lat': 9.0833,  'lng': 36.5500},
    {'name': 'Robe (Bale)',        'lat': 7.1167,  'lng': 40.0000},
    {'name': 'Shashamene',         'lat': 7.2000,  'lng': 38.5833},
    {'name': 'Shire',              'lat': 14.1000, 'lng': 38.2833},
    {'name': 'Sodo (Wolaita)',     'lat': 6.8500,  'lng': 37.7500},
    {'name': 'Woliso',             'lat': 8.5333,  'lng': 37.9833},
    {'name': 'Ziway',              'lat': 7.9333,  'lng': 38.7167},
]


def _fmt_time(t):
    t = t % 24
    h = int(t)
    m = int(round((t - h) * 60))
    if m == 60:
        h += 1
        m = 0
    return f"{h % 24:02d}:{m:02d}"


def _compute_prayer_times(lat, lng, date, fajr_angle=19.5, isha_angle=17.5):
    n      = date.timetuple().tm_yday
    B      = math.radians((360.0 / 365.0) * (n - 81))
    EqT    = (9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)) / 60.0
    decl   = math.radians(23.45 * math.sin(B))
    lat_r  = math.radians(lat)

    utc_offset  = round(lng / 15.0)
    midday_utc  = 12.0 - (lng / 15.0) - EqT

    def hour_angle_below(angle_deg):
        cv = (
            -math.sin(math.radians(angle_deg))
            - math.sin(lat_r) * math.sin(decl)
        ) / (math.cos(lat_r) * math.cos(decl))
        cv = max(-1.0, min(1.0, cv))
        return math.acos(cv) / math.pi * 12.0

    asr_elev_deg = math.degrees(
        math.atan(1.0 / (1.0 + math.tan(abs(lat_r - decl))))
    )
    cv_asr = (
        math.sin(math.radians(asr_elev_deg))
        - math.sin(lat_r) * math.sin(decl)
    ) / (math.cos(lat_r) * math.cos(decl))
    asr_h = math.acos(max(-1.0, min(1.0, cv_asr))) / math.pi * 12.0

    def civil(utc_h):
        return utc_h + utc_offset

    return {
        'Fajr':    _fmt_time(civil(midday_utc - hour_angle_below(fajr_angle))),
        'Dhuhr':   _fmt_time(civil(midday_utc)),
        'Asr':     _fmt_time(civil(midday_utc + asr_h)),
        'Maghrib': _fmt_time(civil(midday_utc + hour_angle_below(0.833))),
        'Isha':    _fmt_time(civil(midday_utc + hour_angle_below(isha_angle))),
    }


def _gregorian_to_hijri(year, month, day):
    if month <= 2:
        y, m = year - 1, month + 12
    else:
        y, m = year, month
    A  = int(y / 100)
    B  = 2 - A + int(A / 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + day + B - 1524
    l  = jd - 1948440 + 10632
    n  = int((l - 1) / 10631)
    l  = l - 10631 * n + 354
    j  = (int((10985 - l) / 5316) * int(50 * l / 17719)
          + int(l / 5670) * int(43 * l / 15238))
    l  = (l - int((30 - j) / 15) * int(17719 * j / 50)
          - int(j / 16) * int(15238 * j / 43) + 29)
    hm = int(24 * l / 709)
    hd = l - int(709 * hm / 24)
    hy = 30 * n + j - 30
    return int(hy), int(hm), int(hd)


def _hijri_to_gregorian(hy, hm, hd):
    n   = hd + int(29.5001 * (hm - 1) + 0.99)
    q   = int((hy - 1) / 30)
    r   = (hy - 1) % 30
    a   = int((11 * r + 3) / 30)
    w   = int(r / 2)
    q1  = int(q / 4)
    b   = int(r / 4)
    nd  = n + a + w - b + q * 10631 + 1948440 - 385 + q1 * 10
    jd  = int(nd) + int(3 * (int((nd + 184) / 36525) + 1) / 4) - 38
    l   = jd + 68569
    n2  = int(4 * l / 146097)
    l   = l - int((146097 * n2 + 3) / 4)
    i   = int(4000 * (l + 1) / 1461001)
    l   = l - int(1461 * i / 4) + 31
    j2  = int(80 * l / 2447)
    gd  = l - int(2447 * j2 / 80)
    l   = int(j2 / 11)
    gm  = j2 + 2 - 12 * l
    gy  = 100 * (n2 - 49) + i + l
    return int(gy), int(gm), int(gd)


def _upcoming_holidays(count=10):
    today = datetime.date.today()
    hy0, _, _ = _gregorian_to_hijri(today.year, today.month, today.day)
    results = []
    for delta_year in range(0, 3):
        for hm, hd, name, icon in ISLAMIC_HOLIDAYS:
            try:
                gy, gm, gd = _hijri_to_gregorian(hy0 + delta_year, hm, hd)
                gdate = datetime.date(gy, gm, gd)
            except Exception:
                continue
            days_away = (gdate - today).days
            if days_away >= 0:
                hy_c, hm_c, hd_c = _gregorian_to_hijri(gy, gm, gd)
                results.append({
                    'name':      name,
                    'icon':      icon,
                    'gregorian': gdate.strftime('%d %b %Y'),
                    'hijri':     f"{hd_c} {HIJRI_MONTHS[hm_c-1]} {hy_c} AH",
                    'days_away': days_away,
                    'is_today':  days_away == 0,
                })
    results.sort(key=lambda x: x['days_away'])
    seen, unique = set(), []
    for r in results:
        k = r['name'] + r['gregorian']
        if k not in seen:
            seen.add(k)
            unique.append(r)
    return unique[:count]


def _safe_coords(lat_str, lng_str):
    try:
        lat = float(lat_str) if lat_str not in (None, '', 'null') else DEFAULT_LAT
        lng = float(lng_str) if lng_str not in (None, '', 'null') else DEFAULT_LNG
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return DEFAULT_LAT, DEFAULT_LNG, True
        if lat == 0.0 and lng == 0.0:
            return DEFAULT_LAT, DEFAULT_LNG, True
        return lat, lng, False
    except (TypeError, ValueError):
        return DEFAULT_LAT, DEFAULT_LNG, True


_QURAN_CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'quran_cache.json')
_quran_data_cache = None


def _load_quran_data():
    global _quran_data_cache
    if _quran_data_cache is not None:
        return _quran_data_cache
    cache_path = os.path.abspath(_QURAN_CACHE_PATH)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                _quran_data_cache = json.load(f)
            return _quran_data_cache
        except Exception:
            pass
    if not _HAS_REQUESTS:
        return None
    try:
        url = 'https://raw.githubusercontent.com/risan/quran-json/main/data/quran.json'
        resp = _requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        _quran_data_cache = data
        return _quran_data_cache
    except Exception:
        return None


@islamic_bp.route('/api/quran/surahs')
def quran_surahs():
    result = []
    for num, arabic, transliteration, meaning, ayahs, revelation in SURAHS:
        reciter = request.args.get('reciter', 'alafasy')
        reciter_data = RECITERS.get(reciter, RECITERS['alafasy'])
        result.append({
            'number':         num,
            'arabic_name':    arabic,
            'transliteration':transliteration,
            'meaning':        meaning,
            'total_ayahs':    ayahs,
            'revelation_type':revelation,
            'audio_url':      reciter_data['urls'][num],
        })
    reciters_list = [{'id': k, 'name': v['name']} for k, v in RECITERS.items()]
    return jsonify({'success': True, 'surahs': result, 'reciters': reciters_list})


@islamic_bp.route('/api/quran/surah/<int:surah_num>')
def quran_surah(surah_num):
    if surah_num < 1 or surah_num > 114:
        return jsonify({'success': False, 'error': 'Surah number must be 1–114'}), 400
    meta = next((s for s in SURAHS if s[0] == surah_num), None)
    if not meta:
        return jsonify({'success': False, 'error': 'Surah not found'}), 404
    num, arabic, transliteration, meaning, total_ayahs, revelation = meta
    reciter = request.args.get('reciter', 'alafasy')
    reciter_data = RECITERS.get(reciter, RECITERS['alafasy'])
    audio_url = reciter_data['urls'][num]
    ayahs = []
    quran_data = _load_quran_data()
    if quran_data:
        try:
            verses_list = None
            if isinstance(quran_data, list):
                if surah_num <= len(quran_data):
                    entry = quran_data[surah_num - 1]
                    if isinstance(entry, list):
                        verses_list = entry
                    elif isinstance(entry, dict):
                        verses_list = entry.get('verses') or entry.get('ayahs') or []
            elif isinstance(quran_data, dict):
                entry = quran_data.get(surah_num) or quran_data.get(str(surah_num))
                if isinstance(entry, list):
                    verses_list = entry
                elif isinstance(entry, dict):
                    verses_list = entry.get('verses') or entry.get('ayahs') or []
            if verses_list:
                for i, v in enumerate(verses_list, 1):
                    if isinstance(v, dict):
                        text = v.get('text') or v.get('arabic') or v.get('ar') or ''
                    else:
                        text = str(v)
                    ayahs.append({'number': i, 'text': text})
        except Exception:
            ayahs = []
    return jsonify({
        'success':          True,
        'number':           num,
        'arabic_name':      arabic,
        'transliteration':  transliteration,
        'meaning':          meaning,
        'total_ayahs':      total_ayahs,
        'revelation_type':  revelation,
        'audio_url':        audio_url,
        'ayahs':            ayahs,
        'has_text':         len(ayahs) > 0,
    })


@islamic_bp.route('/islamic')
def islamic_suite():
    lang  = get_lang()
    today = datetime.date.today()
    hy, hm, hd = _gregorian_to_hijri(today.year, today.month, today.day)
    is_ramadan     = (hm == 9)
    force_ramadan  = request.args.get('ramadan') == '1'
    ramadan_active = is_ramadan or force_ramadan
    hijri_today = {
        'day':   hd,
        'month': HIJRI_MONTHS[hm - 1],
        'year':  hy,
        'full':  f"{hd} {HIJRI_MONTHS[hm-1]} {hy} AH",
    }
    holidays = _upcoming_holidays(10)
    return render_template(
        'customer/islamic.html',
        lang=lang,
        hijri_today=hijri_today,
        holidays=holidays,
        ramadan_active=ramadan_active,
        cities=ETHIOPIAN_CITIES,
    )


@islamic_bp.route('/api/islamic/prayer-times')
def prayer_times_api():
    try:
        lat, lng, used_fallback = _safe_coords(
            request.args.get('lat'),
            request.args.get('lng')
        )
        today = datetime.date.today()
        times = _compute_prayer_times(float(lat), float(lng), today)
        hy, hm, hd = _gregorian_to_hijri(today.year, today.month, today.day)
        return jsonify({
            'success':    True,
            'date':       today.isoformat(),
            'times':      times,
            'lat':        lat,
            'lng':        lng,
            'hijri':      f"{hd} {HIJRI_MONTHS[hm-1]} {hy} AH",
            'is_ramadan': hm == 9,
            'fallback':   used_fallback,
        })
    except Exception:
        current_app.logger.error("Traceback:", exc_info=True)
        return jsonify({
            'success':  True,
            'date':     datetime.date.today().isoformat(),
            'times':    ADDIS_FALLBACK,
            'lat':      DEFAULT_LAT,
            'lng':      DEFAULT_LNG,
            'hijri':    '',
            'fallback': True,
            'static':   True,
        })


@islamic_bp.route('/api/islamic/qibla-direction')
def qibla_direction_api():
    try:
        lat, lng, _ = _safe_coords(
            request.args.get('lat'),
            request.args.get('lng')
        )
        lat  = float(lat)
        lng  = float(lng)
        dlng = math.radians(KAABA_LNG - lng)
        x    = math.sin(dlng) * math.cos(math.radians(KAABA_LAT))
        y    = (math.cos(math.radians(lat)) * math.sin(math.radians(KAABA_LAT))
                - math.sin(math.radians(lat)) * math.cos(math.radians(KAABA_LAT)) * math.cos(dlng))
        bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
        return jsonify({'success': True, 'bearing': round(bearing, 2)})
    except Exception:
        current_app.logger.error("Traceback:", exc_info=True)
        return jsonify({'success': True, 'bearing': 4.61})


@islamic_bp.route('/api/islamic/monthly-prayer-times')
def monthly_prayer_times():
    try:
        lat, lng, _ = _safe_coords(
            request.args.get('lat'),
            request.args.get('lng')
        )
        today  = datetime.date.today()
        year   = int(request.args.get('year',  today.year))
        month  = int(request.args.get('month', today.month))
        days_in_month = cal_module.monthrange(year, month)[1]
        result = []
        for d in range(1, days_in_month + 1):
            date  = datetime.date(year, month, d)
            times = _compute_prayer_times(float(lat), float(lng), date)
            hy, hm, hd = _gregorian_to_hijri(date.year, date.month, date.day)
            result.append({
                'day':         d,
                'weekday':     date.strftime('%a'),
                'hijri_day':   hd,
                'hijri_month': HIJRI_MONTHS[hm - 1],
                'times':       times,
            })
        return jsonify({'success': True, 'days': result, 'month': month, 'year': year})
    except Exception:
        current_app.logger.error("Traceback:", exc_info=True)
        return jsonify({'success': False, 'error': 'Calculation error'}), 500


@islamic_bp.route('/api/islamic/prayer-schedule-csv')
def prayer_schedule_csv():
    try:
        lat, lng, _ = _safe_coords(
            request.args.get('lat'),
            request.args.get('lng')
        )
        today  = datetime.date.today()
        year   = int(request.args.get('year',  today.year))
        month  = int(request.args.get('month', today.month))
        days_in_month = cal_module.monthrange(year, month)[1]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Hijri Date', 'Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'])
        for d in range(1, days_in_month + 1):
            date  = datetime.date(year, month, d)
            times = _compute_prayer_times(float(lat), float(lng), date)
            hy, hm, hd = _gregorian_to_hijri(date.year, date.month, date.day)
            writer.writerow([
                date.strftime('%d %b %Y'),
                f"{hd} {HIJRI_MONTHS[hm-1]} {hy}",
                times['Fajr'], times['Dhuhr'], times['Asr'],
                times['Maghrib'], times['Isha'],
            ])
        output.seek(0)
        month_name = datetime.date(year, month, 1).strftime('%B_%Y')
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename="prayer_times_{month_name}.csv"'}
        )
    except Exception:
        current_app.logger.error("Traceback:", exc_info=True)
        return jsonify({'success': False, 'error': 'Export failed'}), 500

"""
Language Middleware for SEMIRA FASHION

This module handles multi-language support for the application.
Supports Amharic (አማርኛ), English, and Arabic (العربية).
Uses Google Translate widget for free translation.
"""

from functools import wraps
from flask import request, session, g, redirect, url_for
import re


# ==================== LANGUAGE CONFIGURATION ====================

LANGUAGES = {
    'am': {
        'code': 'am',
        'name': 'አማርኛ',
        'flag': '🇪🇹',
        'direction': 'ltr',
        'google_code': 'am'
    },
    'en': {
        'code': 'en',
        'name': 'English',
        'flag': '🇬🇧',
        'direction': 'ltr',
        'google_code': 'en'
    },
    'ar': {
        'code': 'ar',
        'name': 'العربية',
        'flag': '🇸🇦',
        'direction': 'rtl',
        'google_code': 'ar'
    }
}

DEFAULT_LANGUAGE = 'am'


# ==================== LANGUAGE HELPER FUNCTIONS ====================

def get_browser_language():
    """
    Detect browser language from Accept-Language header.
    
    Returns:
        str: Language code (am, en, ar) or None
    """
    accept_language = request.headers.get('Accept-Language', '')
    
    # Parse Accept-Language header
    languages = []
    for lang in accept_language.split(','):
        lang = lang.strip().split(';')[0].split('-')[0]
        if lang in LANGUAGES:
            languages.append(lang)
    
    # Return first matching language or None
    return languages[0] if languages else None


def get_saved_language():
    """
    Get saved language from session or cookie.
    
    Returns:
        str: Language code or None
    """
    # Check session first
    lang = session.get('language')
    if lang and lang in LANGUAGES:
        return lang
    
    # Check cookie
    lang = request.cookies.get('language')
    if lang and lang in LANGUAGES:
        return lang
    
    return None


def set_language(lang_code):
    """
    Set language in session.
    
    Args:
        lang_code (str): Language code (am, en, ar)
    
    Returns:
        bool: True if valid, False otherwise
    """
    if lang_code in LANGUAGES:
        session['language'] = lang_code
        session.permanent = True
        return True
    return False


def get_current_language():
    """
    Get current active language.
    Priority: Session/Cookie > Browser > Default
    
    Returns:
        dict: Language information
    """
    lang_code = get_saved_language()
    
    if not lang_code:
        lang_code = get_browser_language()
    
    if not lang_code or lang_code not in LANGUAGES:
        lang_code = DEFAULT_LANGUAGE
    
    return {
        'code': lang_code,
        **LANGUAGES[lang_code]
    }


def get_google_translate_widget():
    """
    Generate Google Translate widget HTML.
    This is a free widget that doesn't require API key.
    
    Returns:
        str: HTML for Google Translate widget
    """
    current_lang = get_current_language()
    
    return f'''
    <div id="google_translate_element" class="google-translate-widget"></div>
    <script type="text/javascript">
        // Google Translate Widget Configuration
        function googleTranslateElementInit() {{
            new google.translate.TranslateElement({{
                pageLanguage: '{current_lang["google_code"]}',
                includedLanguages: 'am,en,ar',
                layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
                autoDisplay: false,
                multilanguagePage: true
            }}, 'google_translate_element');
        }}
        
        // Store original language preference
        function setLanguagePreference(lang) {{
            document.cookie = "language=" + lang + "; path=/; max-age=31536000";
            // Reload page to apply language
            window.location.reload();
        }}
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
    '''


def get_language_selector_html():
    """
    Generate language selector dropdown HTML.
    
    Returns:
        str: HTML for language selector
    """
    current = get_current_language()
    
    html = '<div class="language-selector">\n'
    html += '<select id="language-select" onchange="switchLanguage(this.value)">\n'
    
    for code, lang in LANGUAGES.items():
        selected = 'selected' if code == current['code'] else ''
        html += f'<option value="{code}" {selected}>{lang["flag"]} {lang["name"]}</option>\n'
    
    html += '</select>\n'
    html += '</div>\n'
    
    # Add JavaScript for language switching
    html += '''
    <script>
        function switchLanguage(langCode) {
            fetch('/set-language/' + langCode, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload page to apply new language
                    window.location.reload();
                }
            })
            .catch(error => console.error('Error:', error));
        }
        
        // Save language preference when Google Translate changes
        document.addEventListener('DOMContentLoaded', function() {
            // Wait for Google Translate to load
            setTimeout(function() {
                var select = document.querySelector('.goog-te-combo');
                if (select) {
                    select.addEventListener('change', function() {
                        var lang = this.value;
                        if (lang) {
                            setLanguagePreference(lang);
                        }
                    });
                }
            }, 2000);
        });
    </script>
    '''
    
    return html


# ==================== TRANSLATION HELPERS ====================

def translate_text(text, target_lang=None):
    """
    Simple text translation using Google Translate.
    Note: This is a basic implementation. For production,
    consider using Google Translate API or similar.
    
    Args:
        text (str): Text to translate
        target_lang (str): Target language code
    
    Returns:
        str: Translated text (or original if translation fails)
    """
    # For now, return original text
    # Google Translate widget handles frontend translation
    return text


def get_translated_field(obj, field_en, field_am=None, field_ar=None, lang=None):
    """
    Get translated field value from object.
    
    Args:
        obj: Database object or dict
        field_en (str): English field name
        field_am (str, optional): Amharic field name
        field_ar (str, optional): Arabic field name
        lang (str, optional): Target language
    
    Returns:
        str: Translated value
    """
    if not lang:
        lang = get_current_language()['code']
    
    # Determine which field to use based on language
    field_name = field_en
    if lang == 'am' and field_am:
        field_name = field_am
    elif lang == 'ar' and field_ar:
        field_name = field_ar
    
    # Get value from object
    if isinstance(obj, dict):
        return obj.get(field_name, obj.get(field_en, ''))
    else:
        return getattr(obj, field_name, getattr(obj, field_en, ''))
    
    return ''


# ==================== TEMPLATE CONTEXT PROCESSOR ====================

def add_language_context():
    """
    Add language context to templates.
    This function should be called from app context processor.
    
    Returns:
        dict: Language context variables
    """
    current_lang = get_current_language()
    
    return {
        'current_language': current_lang,
        'languages': LANGUAGES,
        'language_selector': get_language_selector_html(),
        'google_translate_widget': get_google_translate_widget(),
        't': get_translated_field,  # Shortcut for template translation
        'is_rtl': current_lang['code'] == 'ar'
    }


# ==================== MIDDLEWARE ====================

def language_middleware():
    """
    Process language for each request.
    Sets g.lang with current language info.
    """
    current_lang = get_current_language()
    g.lang = current_lang
    g.is_rtl = current_lang['code'] == 'ar'


# ==================== ROUTES ====================

def register_language_routes(app):
    """
    Register language-related routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/set-language/<lang_code>', methods=['POST'])
    def set_language_route(lang_code):
        """Endpoint to change language"""
        from flask import jsonify
        
        if set_language(lang_code):
            return jsonify({
                'success': True,
                'language': lang_code,
                'message': f'Language changed to {LANGUAGES[lang_code]["name"]}'
            })
        
        return jsonify({
            'success': False,
            'error': 'Invalid language code'
        }), 400
    
    @app.route('/get-language')
    def get_language_route():
        """Endpoint to get current language"""
        from flask import jsonify
        
        current = get_current_language()
        return jsonify({
            'success': True,
            'language': current
        })


# ==================== RTL SUPPORT ====================

def get_rtl_css():
    """
    Get RTL CSS for Arabic language.
    
    Returns:
        str: CSS for RTL layout
    """
    return '''
    /* RTL Layout for Arabic */
    html[dir="rtl"] body {
        text-align: right;
    }
    
    html[dir="rtl"] .language-selector {
        direction: ltr;
    }
    
    html[dir="rtl"] .navbar-nav {
        padding-right: 0;
    }
    
    html[dir="rtl"] .ml-auto {
        margin-right: auto !important;
        margin-left: 0 !important;
    }
    
    html[dir="rtl"] .mr-auto {
        margin-left: auto !important;
        margin-right: 0 !important;
    }
    
    html[dir="rtl"] .text-left {
        text-align: right !important;
    }
    
    html[dir="rtl"] .text-right {
        text-align: left !important;
    }
    '''


def get_rtl_js():
    """
    Get JavaScript for RTL support.
    
    Returns:
        str: JavaScript for RTL layout
    """
    return '''
    // Set RTL attribute for Arabic language
    function setRTL() {
        var lang = document.documentElement.lang || 'am';
        var rtlLangs = ['ar'];
        
        if (rtlLangs.includes(lang)) {
            document.documentElement.setAttribute('dir', 'rtl');
        } else {
            document.documentElement.setAttribute('dir', 'ltr');
        }
    }
    
    // Call on page load
    document.addEventListener('DOMContentLoaded', setRTL);
    '''


# ==================== INITIALIZATION ====================

def init_language(app):
    """
    Initialize language support for the app.
    
    Args:
        app: Flask application instance
    """
    # Register language routes
    register_language_routes(app)
    
    # Add context processor
    app.context_processor(add_language_context)
    
    # Add before request handler
    @app.before_request
    def before_request():
        language_middleware()
    
    print("✅ Language middleware initialized (Amharic, English, Arabic)")
    print("   - Google Translate widget available")
    print("   - RTL support for Arabic")
from flask import request


def get_platform():
    """Detect the platform based on User-Agent and custom headers."""
    user_agent = request.headers.get('User-Agent', '').lower()
    x_platform = request.headers.get('X-Platform', '').lower()

    if x_platform == 'android' or 'semirafashion-android' in user_agent:
        return 'android'
    if 'android' in user_agent:
        return 'android_browser'
    if 'iphone' in user_agent or 'ipad' in user_agent:
        return 'ios'
    if 'mobile' in user_agent:
        return 'mobile'
    return 'desktop'


def is_android_app():
    """Return True if the request is from the native Android app."""
    user_agent = request.headers.get('User-Agent', '').lower()
    x_platform = request.headers.get('X-Platform', '').lower()
    return x_platform == 'android' or 'semirafashion-android' in user_agent


def is_mobile_browser():
    """Return True if the request is from a mobile browser (not native app)."""
    if is_android_app():
        return False
    user_agent = request.headers.get('User-Agent', '').lower()
    return any(kw in user_agent for kw in ('android', 'iphone', 'ipad', 'mobile'))


def is_desktop():
    """Return True if the request is from a desktop browser."""
    return get_platform() == 'desktop'

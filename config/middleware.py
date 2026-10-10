"""Project middleware."""
from django.conf import settings


class DefaultEnglishMiddleware:
    """Force English as the default UI language.

    Django's LocaleMiddleware normally honours the browser's Accept-Language
    header, so an Uzbek/Russian browser would see the site in uz/ru even though
    English is the intended default. This middleware neutralises that header for
    visitors who have NOT explicitly chosen a language (no language cookie) and
    are on a non-prefixed URL, so LocaleMiddleware falls back to LANGUAGE_CODE
    ('en'). Explicit choices — the /uz/ /ru/ URL prefixes and the language cookie
    set by the switcher — are always respected.
    """

    PREFIXES = ('/uz/', '/ru/', '/en/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cookie_name = getattr(settings, 'LANGUAGE_COOKIE_NAME', 'django_language')
        path = request.path_info
        has_prefix = path.startswith(self.PREFIXES)
        if cookie_name not in request.COOKIES and not has_prefix:
            request.META['HTTP_ACCEPT_LANGUAGE'] = 'en'
        return self.get_response(request)

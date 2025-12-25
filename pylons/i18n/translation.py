"""Minimal i18n translation helper for the Pylons shim.

Provides `_get_translator(lang)` which returns an object with gettext-like
methods. If Babel is available it will use Babel translations; otherwise it
falls back to a no-op translator.
"""

try:
    from babel.support import Translations
except Exception:
    Translations = None


class _NoopTranslator:
    def gettext(self, s):
        return s

    def ugettext(self, s):
        return s

    def ngettext(self, singular, plural, n):
        return singular if n == 1 else plural


def _get_translator(lang=None):
    """Return a translator object for the given language.

    This intentionally returns a minimal translator that supports the calls
    tests and the codebase make (gettext / ugettext / ngettext).
    """
    if Translations is None:
        return _NoopTranslator()
    try:
        # Construct a simple Translations object if message catalogs exist on
        # the environment; otherwise fall back to no-op translator.
        return Translations.load(locale=lang) if lang else Translations()
    except Exception:
        return _NoopTranslator()

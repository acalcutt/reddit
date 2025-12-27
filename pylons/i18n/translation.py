"""Minimal i18n translation helper for the Pylons shim.

Provides `_get_translator(lang)` which returns an object with gettext-like
methods. If Babel is available it will use Babel translations; otherwise it
falls back to a no-op translator.
"""
import gettext as gettext_module
import os

try:
    from babel.support import Translations as BabelTranslations
except Exception:
    BabelTranslations = None


class LanguageError(Exception):
    """Exception raised when a language cannot be found or loaded."""
    pass


class NullTranslations(gettext_module.NullTranslations):
    """A translations class that doesn't translate anything.

    This is used as a fallback when no translations are available.
    """

    def ugettext(self, message):
        """Unicode version of gettext."""
        return message

    def ungettext(self, singular, plural, n):
        """Unicode version of ngettext."""
        return singular if n == 1 else plural


class _NoopTranslator:
    def gettext(self, s):
        return s

    def ugettext(self, s):
        return s

    def ngettext(self, singular, plural, n):
        return singular if n == 1 else plural

    def ungettext(self, singular, plural, n):
        return singular if n == 1 else plural


def _get_translator(lang=None):
    """Return a translator object for the given language.

    This intentionally returns a minimal translator that supports the calls
    tests and the codebase make (gettext / ugettext / ngettext).
    """
    if BabelTranslations is None:
        return _NoopTranslator()
    try:
        # Construct a simple Translations object if message catalogs exist on
        # the environment; otherwise fall back to no-op translator.
        return BabelTranslations.load(locale=lang) if lang else BabelTranslations()
    except Exception:
        return _NoopTranslator()


def translation(lang, localedir=None, languages=None, class_=None,
                fallback=False, domain='messages'):
    """Get a translations object for the given language.

    This is a compatibility function that mimics Pylons' translation() function.

    Args:
        lang: Language code (e.g., 'en', 'fr')
        localedir: Directory containing locale files
        languages: List of languages to try
        class_: Translation class to use (defaults to NullTranslations)
        fallback: If True, return NullTranslations on failure
        domain: The message domain

    Returns:
        A translations object

    Raises:
        LanguageError: If the language cannot be found and fallback is False
    """
    if languages is None:
        languages = [lang] if lang else []

    if class_ is None:
        class_ = NullTranslations

    # Try to load translations using gettext
    try:
        if localedir and os.path.isdir(localedir):
            return gettext_module.translation(
                domain,
                localedir=localedir,
                languages=languages,
                class_=class_,
                fallback=fallback,
            )
    except Exception:
        pass

    # Try Babel if available
    if BabelTranslations is not None:
        try:
            return BabelTranslations.load(dirname=localedir, locales=languages, domain=domain)
        except Exception:
            pass

    if fallback:
        return NullTranslations()

    raise LanguageError(f"Could not load translations for language: {lang}")


__all__ = [
    '_get_translator', '_NoopTranslator', 'LanguageError', 'NullTranslations',
    'translation',
]

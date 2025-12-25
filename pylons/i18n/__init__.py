"""Pylons i18n compatibility shim.

Provides `_`, `ungettext`, and other i18n functions that mimic Pylons' i18n API.
These functions use a thread-local translator that can be set per-request.
"""
from threading import local

from .translation import _get_translator, _NoopTranslator

# Thread-local storage for the current translator
_translator_local = local()


def get_translator():
    """Get the current thread-local translator."""
    translator = getattr(_translator_local, 'translator', None)
    if translator is None:
        translator = _NoopTranslator()
        _translator_local.translator = translator
    return translator


def set_translator(translator):
    """Set the current thread-local translator."""
    _translator_local.translator = translator


def _(message):
    """Mark a string for translation and translate it.

    This is the primary translation function, equivalent to gettext.
    """
    return get_translator().gettext(message)


def ungettext(singular, plural, n):
    """Translate a string with plural forms.

    Returns the singular form if n == 1, otherwise the plural form.
    """
    return get_translator().ngettext(singular, plural, n)


def ugettext(message):
    """Unicode version of gettext (same as _ in Python 3)."""
    return get_translator().gettext(message)


def ngettext(singular, plural, n):
    """Alias for ungettext."""
    return ungettext(singular, plural, n)


def N_(message):
    """Mark a string for translation without translating it.

    Used for lazy translation where the actual translation happens later.
    """
    return message


def lazy_ugettext(message):
    """Lazy version of ugettext that defers translation."""
    # For now, just return the translated string immediately
    # A full implementation would return a lazy proxy object
    return ugettext(message)


__all__ = [
    '_', 'ungettext', 'ugettext', 'ngettext', 'N_', 'lazy_ugettext',
    'get_translator', 'set_translator', '_get_translator',
]

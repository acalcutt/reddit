# Minimal shim for unidecode package used during tests when not installed.
# Provide `unidecode` function that returns a simplified ASCII string.

def unidecode(text):
    try:
        if isinstance(text, (bytes, bytearray)):
            text = text.decode('utf-8', 'ignore')
    except Exception:
        pass
    # Very small best-effort: strip non-ascii characters
    return ''.join(ch for ch in text if ord(ch) < 128)

__all__ = ['unidecode']

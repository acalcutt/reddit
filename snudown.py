# Minimal stub for snudown to allow tests to run without the native extension
import html

RENDERER_WIKI = 'wiki'

def markdown(text, nofollow=False, target=None, renderer=None, **kwargs):
    if text is None:
        return ''
    # Accept bytes
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8')
        except Exception:
            text = text.decode('latin-1')
    # Very small markdown fallback: escape HTML and wrap in a div
    safe = html.escape(text)
    # preserve simple newlines as <br/>
    safe = safe.replace('\n', '<br/>')
    return safe

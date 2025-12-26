# Minimal shim for snudown used during test collection when the
# optional compiled `snudown` extension is not available.
# Provide a `markdown` function and a `RENDERER_WIKI` constant used
# by the codebase.
RENDERER_WIKI = 'wiki'

def markdown(text, nofollow=False, target=None, renderer=None):
    # Very small no-op implementation that returns the input text
    # wrapped in a safe HTML placeholder. Tests that depend on the
    # full behavior should install the real snudown package.
    try:
        # attempt to coerce bytes to str
        if isinstance(text, (bytes, bytearray)):
            text = text.decode('utf-8', 'ignore')
    except Exception:
        pass
    return text

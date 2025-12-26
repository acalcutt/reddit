def unidecode(s):
    if s is None:
        return ''
    if isinstance(s, bytes):
        try:
            s = s.decode('utf-8')
        except Exception:
            s = s.decode('latin-1')
    try:
        return s.encode('ascii', 'ignore').decode('ascii')
    except Exception:
        return str(s)

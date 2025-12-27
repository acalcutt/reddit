"""Pure-Python fallback for the Cython `wrapped.pyx` implementation.

This provides minimal implementations of `Templated`, `CachedTemplate`,
`Wrapped`, and `Styled` sufficient for import-time use during tests
and for basic rendering paths. It intentionally implements a subset of
the original behaviour to avoid requiring C compilation in test CI.
"""
from datetime import datetime
import random
import types

class StringTemplate:
    start_delim = "<$>"
    end_delim = "</$>"

    def __init__(self, template):
        if template is None:
            template = ''
        self.template = str(template)

    def update(self, d):
        # naive replacement for keys that appear as start_delim+name+end_delim
        s = self.template
        if d:
            for k, v in d.items():
                s = s.replace(self.start_delim + str(k) + self.end_delim, str(v))
        return StringTemplate(s)

    def finalize(self, d=None):
        if d:
            return self.update(d).template
        return self.template


class CacheStub:
    def __init__(self, item, style):
        self.name = "h%s%s" % (id(item), str(style).replace('-', '_'))

    def __str__(self):
        return StringTemplate.start_delim + self.name + StringTemplate.end_delim

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)


class CachedVariable(CacheStub):
    def __init__(self, name):
        self.name = name


class Templated(object):
    cachable = False
    cache_ignore = set()

    def __init__(self, **context):
        for k, v in context.items():
            setattr(self, k, v)
        if not hasattr(self, 'render_class'):
            self.render_class = self.__class__

    def template(self, style='html'):
        # return a very small dummy template object with a render() method
        class DummyTemplate:
            def __init__(self, tpl=''):
                self.tpl = tpl

            def render(self, **kwargs):
                return StringTemplate(self.tpl)

            @property
            def is_null(self):
                return False

        return DummyTemplate('')

    def template_is_null(self, style='html'):
        return getattr(self.template(style), 'is_null', False)

    def render_nocache(self, style):
        # minimal timing/no-op behavior and return a StringTemplate
        template = self.template(style)
        res = template.render(thing=self)
        if not isinstance(res, StringTemplate):
            res = StringTemplate(res)
        return res

    def _render(self, style=None, **kwargs):
        # Simplified rendering: always render without caching
        res = self.render_nocache(style or 'html')
        if isinstance(res, StringTemplate):
            return res.finalize(kwargs)
        return res

    def render(self, style=None, **kw):
        return self._render(style, **kw)


class CachedTemplate(Templated):
    cachable = True

    def cache_key(self, style):
        # lightweight cache key based on class name
        return "rend:%s" % (self.render_class.__name__,)


class Wrapped(CachedTemplate):
    cachable = False
    cache_ignore = set(['lookups'])

    def __init__(self, *lookups, **context):
        self.lookups = lookups
        if self.__class__ == Wrapped and lookups:
            self.render_class = lookups[0].__class__
        else:
            self.render_class = self.__class__
        self.cache_ignore = self.cache_ignore.union(set(['cachable', 'render', 'cache_ignore', 'lookups']))
        Templated.__init__(self, **context)

    def _any_hasattr(self, lookups, attr):
        for l in lookups:
            if hasattr(l, attr):
                return True

    def __repr__(self):
        return "<Wrapped: %s,  %s>" % (self.__class__.__name__, self.lookups)

    def __getattr__(self, attr):
        if attr == 'lookups':
            raise AttributeError(attr)
        for lookup in self.lookups:
            try:
                res = getattr(lookup, attr)
                setattr(self, attr, res)
                return res
            except AttributeError:
                continue
        raise AttributeError("%r has no %s" % (self, attr))

    def __iter__(self):
        if self.lookups and hasattr(self.lookups[0], '__iter__'):
            return iter(self.lookups[0])
        raise NotImplementedError


class Styled(CachedTemplate):
    def __init__(self, style, _id='', css_class='', **kw):
        self._id = _id
        self.css_class = css_class
        self.style = style
        super().__init__(**kw)

    def template(self, style='html'):
        base_template = super().template(style)
        # best-effort: return base_template (dummy)
        return base_template


def make_cachable(v, style):
    # best-effort serializer for cache keys
    if v is None:
        return 'None'
    if isinstance(v, (bool, int, float, str)):
        return str(v)
    if isinstance(v, (list, tuple, set)):
        return repr([make_cachable(x, style) for x in v])
    if isinstance(v, dict):
        return repr({k: make_cachable(v[k], style) for k in sorted(v)})
    if hasattr(v, 'cache_key'):
        try:
            return v.cache_key(style)
        except Exception:
            return repr(v)
    return repr(v)

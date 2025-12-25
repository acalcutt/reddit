import pylons
from pylons.i18n.translation import _get_translator


def test_config_push_and_get():
    # ensure no object is pushed initially
    assert not bool(pylons.config)
    assert pylons.config.get('nonexistent', 'default') == 'default'

    pylons.config._push_object({'lang': 'en', 'foo': 'bar'})
    assert pylons.config.get('lang') == 'en'
    assert pylons.config['foo'] == 'bar'

    pylons.config._pop_object()
    assert pylons.config.get('lang') is None


def test_translator_push_and_get():
    trans = _get_translator('en')
    # translator should expose gettext-like API
    assert hasattr(trans, 'gettext')

    pylons.translator._push_object(trans)
    assert hasattr(pylons.translator._stack[-1], 'gettext')
    pylons.translator._pop_object()

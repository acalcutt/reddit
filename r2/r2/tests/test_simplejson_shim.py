import json
import simplejson


def test_simplejson_shim_dumps_loads():
    obj = {"a": 1, "b": [1, 2, 3]}
    s1 = json.dumps(obj, sort_keys=True)
    s2 = simplejson.dumps(obj, sort_keys=True)
    assert s1 == s2
    assert simplejson.loads(s2) == obj

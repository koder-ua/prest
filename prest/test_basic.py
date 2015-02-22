import contextlib

from oktest import ok

from prest import PRestBase, GET, POST, PUT, PATCH, DELETE


class HTTPOK(object):
    def __init__(self, mock):
        self.mock = mock

    def __eq__(self, val):
        ok(self.mock.popleft()) == val
        return True


class HTTPMock(object):
    default_res = {}

    def __init__(self, url=""):
        self.history = []
        self.responce = self.default_res.copy()

    def popleft(self):
        res = self.history[0]
        del self.history[0]
        return res

    def post(self, url, params):
        self.history.append(('post', url, params))
        return self.responce.copy()

    def head(self, url, params):
        self.history.append(('head', url, params))
        return self.responce.copy()

    def delete(self, url, params):
        self.history.append(('delete', url, params))
        return self.responce.copy()

    def get(self, url, params=None):
        self.history.append(('get', url, params))
        return self.responce.copy()

    def put(self, url, params):
        self.history.append(('put', url, params))
        return self.responce.copy()

    def patch(self, url, params):
        self.history.append(('patch', url, params))
        return self.responce.copy()

    def ok_http(self, http_res):
        ok(http_res) == self.responce
        return HTTPOK(self)


@contextlib.contextmanager
def raises(exc_class):
    try:
        yield
    except exc_class:
        pass
    except Exception as x:
        templ = "{0} exception get, while instance of {1} expected"
        raise AssertionError(templ.format(x, exc_class))
    else:
        templ = "No exception raised, while instance of {0} expected"
        raise AssertionError(templ.format(exc_class))


class TestBasic(object):
    def test_positional_param_in_urls(self):
        with raises(ValueError):
            GET("x/{0}")

    def test_missing_param(self):
        conn = HTTPMock()

        func = GET("x/{test}")
        with raises(ValueError):
            func(conn)

    def test_extra_param_with_whole_doc(self):
        conn = HTTPMock()

        func = GET("x/{test}")
        with raises(ValueError):
            func(conn, {}, test=12, extra=14)

    def test_missing_param_with_obj(self):
        conn = HTTPMock()

        class TestAPI(PRestBase):
            func = GET("x/{test}")

        api = TestAPI(conn)

        with raises(ValueError):
            api.func()

    def test_get_param_from_obj(self):
        conn = HTTPMock()
        hok = conn.ok_http

        class TestAPI(PRestBase):
            func = GET("x/{test}")

        api = TestAPI(conn)
        api.test = 12

        hok(api.func()) == ('get', 'x/12', {})

    def test_pack_extra_params(self):
        conn = HTTPMock()
        hok = conn.ok_http

        class TestAPI(PRestBase):
            func = GET("x/{test}")

        api = TestAPI(conn)
        api.test = 12

        hok(api.func(a='23')) == ('get', 'x/12', {'a': '23'})

    def test_whole_doc(self):
        conn = HTTPMock()
        hok = conn.ok_http

        class TestAPI(PRestBase):
            func = GET("x/{test}")

        api = TestAPI(conn)

        hok(api.func({'m': 'k'}, test='23')) == ('get', 'x/23', {'m': 'k'})

    def test_api_class(self):
        hm = HTTPMock()
        hok = hm.ok_http

        class API(PRestBase):
            get_docs = GET('docs')
            create_doc = POST('docs')
            update_doc = PUT('docs/{id}')
            delete_doc = DELETE('docs/{id}')
            patch_doc = PATCH('docs/{id}')

        a = API(hm)
        hok(a.get_docs()) == ('get', 'docs', {})

        hm.responce = {'id': 12}
        hok(a.create_doc(x=2)) == ('post', 'docs', {'x': 2})
        hok(a.update_doc(id=12, x=2)) == ('put', 'docs/12', {'x': 2})
        hok(a.delete_doc(id=3, x=2)) == ('delete', 'docs/3', {'x': 2})
        hok(a.patch_doc(id=12, x=2)) == ('patch', 'docs/12', {'x': 2})

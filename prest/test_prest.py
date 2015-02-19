import contextlib

from oktest import ok

from prest import APIClass, GET, POST, PUT, PATCH, DELETE
from prest import ORMBase, attr, restfull_url_set, SAME, OrmHTTPMixIn


class HTTPOK(object):
    def __init__(self, mock):
        self.mock = mock

    def __eq__(self, val):
        ok(self.mock.popleft()) == val
        return True


class HTTPMock(OrmHTTPMixIn):
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


def test_api_class():
    hm = HTTPMock()
    hok = hm.ok_http

    class API(APIClass):
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


@contextlib.contextmanager
def raises(exc_class):
    try:
        yield
    except exc_class:
        pass
    except Exception as x:
        templ = "{} exception get, while instance of {} expected"
        raise AssertionError(templ.format(x, exc_class))
    else:
        templ = "No exception raised, while instance of {} expected"
        raise AssertionError(templ.format(exc_class))


class Msg(ORMBase):
    __urls__ = restfull_url_set('api')


def make_http():
    http = HTTPMock("")
    http.responce = {'id': 12, 'field1': 'xxx', 'field2': 'yyy'}
    return http


def test_orm_create():
    http = make_http()

    m = Msg.make(http, field='xxx')
    m.save()

    ok(http.popleft()) == ('post', 'api', {'field': 'xxx'})
    ok(m.id) == 12
    ok(m.field) == 'xxx'

    with raises(IndexError):
        http.popleft()


def test_orm_load():
    http = make_http()

    m = http.load(Msg, 12)
    ok(http.popleft()) == ('get', 'api/12', None)
    ok(m.id) == 12
    ok(m.field1) == 'xxx'
    ok(m.field2) == 'yyy'

    with raises(IndexError):
        http.popleft()


def test_orm_update():
    http = make_http()

    m = http.load(Msg, 12)
    ok(http.popleft()) == ('get', 'api/12', None)

    m.field1 = 'fff'
    m.save()
    ok(http.popleft()) == ('patch', 'api/12', {'field1': 'fff'})
    with raises(IndexError):
        http.popleft()


def test_orm_add_field():
    http = make_http()

    m = http.load(Msg, 12)
    ok(http.popleft()) == ('get', 'api/12', None)

    m.field3 = 'fff'
    m.save()
    ok(http.popleft()) == ('patch', 'api/12', {'field3': 'fff'})
    with raises(IndexError):
        http.popleft()


def test_orm_rm_field():
    http = make_http()

    m = http.load(Msg, 12)
    ok(http.popleft()) == ('get', 'api/12', None)

    ok(m.field1) == 'xxx'
    del m.field1

    m.save()
    ok(http.popleft()) == ('put', 'api/12', {'field2': 'yyy'})
    with raises(IndexError):
        http.popleft()


def test_orm_attrs():
    http = make_http()

    class Msg(ORMBase):
        __urls__ = restfull_url_set('api')
        ro_data = attr('api/{id}/ro_attr')
        rw_data = attr('api/{id}/rw_attr', SAME)

    http.responce = {'id': 12, 'field': 'xxx'}
    m = http.load(Msg, 1)
    ok(http.popleft()) == ('get', 'api/1', None)
    ok(m.id) == 12
    ok(m.field) == 'xxx'
    ok(m.ro_data.id) == 12
    ok(m.ro_data.field) == 'xxx'
    ok(http.popleft()) == ('get', 'api/12/ro_attr', None)
    m.rw_data['field'] = 18
    ok(http.popleft()) == ('get', 'api/12/rw_attr', None)
    m.rw_data.save()
    ok(http.popleft()) == ('put', 'api/12/rw_attr', {'field': 18})

    m.rw_data['field'] = 19
    m.save()
    ok(http.popleft()) == ('put', 'api/12/rw_attr', {'field': 19})


def test_orm_attr_save():
    http = make_http()

    class Msg(ORMBase):
        __urls__ = restfull_url_set('api')
        ro_data = attr('api/{id}/ro_attr')
        rw_data = attr('api/{id}/rw_attr', SAME)

    http.responce = {'id': 12, 'field': 'xxx'}
    m = http.load(Msg, 1)

    x = m.data
    x.f = 12
    x.test = 13
    x.save()
    ok(http.popleft()) == ('put', 'api/12/rw_attr', {'field': 19})


def test_diff_in_put():
    http = make_http()

    class Msg(ORMBase):
        __urls__ = restfull_url_set('api')
        ro_data = attr('api/{id}/ro_attr')
        rw_data = attr('api/{id}/rw_attr', SAME)

    http.responce = {'id': 12, 'field': 'xxx'}
    m = http.load(Msg, 1)

    x = m.data
    x.f = 12
    x.test = 13
    x.save()
    ok(http.popleft()) == ('put', 'api/12/rw_attr', {'field': 19})


def test_diff_in_patch():
    pass


def test_no_partial_updates():
    pass


def test_derived_class():
    pass

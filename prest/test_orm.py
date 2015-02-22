from oktest import ok


from prest import *
from prest.test_basic import HTTPMock, raises


class ORMHTTPMock(HTTPMock, OrmHTTPMixIn):
    pass


class Msg(ORMBase):
    __urls__ = restfull_url_set('api')


def make_http():
    http = ORMHTTPMock("")
    http.responce = {'id': 12, 'field1': 'xxx', 'field2': 'yyy'}
    return http


class TestORM(object):
    def test_orm_create(self):
        http = make_http()

        m = Msg.make(http, field='xxx')
        m.save()

        ok(http.popleft()) == ('post', 'api', {'field': 'xxx'})
        ok(m.id) == 12
        ok(m.field) == 'xxx'

        with raises(IndexError):
            http.popleft()

    def test_orm_load(self):
        http = make_http()

        m = http.load(Msg, 12)
        ok(http.popleft()) == ('get', 'api/12', None)
        ok(m.id) == 12
        ok(m.field1) == 'xxx'
        ok(m.field2) == 'yyy'

        with raises(IndexError):
            http.popleft()

    def test_orm_update(self):
        http = make_http()

        m = http.load(Msg, 12)
        ok(http.popleft()) == ('get', 'api/12', None)

        m.field1 = 'fff'
        m.save()
        ok(http.popleft()) == ('patch', 'api/12', {'field1': 'fff'})
        with raises(IndexError):
            http.popleft()

    def test_orm_add_field(self):
        http = make_http()

        m = http.load(Msg, 12)
        ok(http.popleft()) == ('get', 'api/12', None)

        m.field3 = 'fff'
        m.save()
        ok(http.popleft()) == ('patch', 'api/12', {'field3': 'fff'})
        with raises(IndexError):
            http.popleft()

    def test_orm_rm_field(self):
        http = make_http()

        m = http.load(Msg, 12)
        ok(http.popleft()) == ('get', 'api/12', None)

        ok(m.field1) == 'xxx'
        del m.field1

        m.save()
        ok(http.popleft()) == ('put', 'api/12', {'field2': 'yyy'})
        with raises(IndexError):
            http.popleft()

    def test_orm_attrs(self):
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
        ok(http.popleft()) == ('patch', 'api/12/rw_attr', {'field': 18})

        m.rw_data['field'] = 19
        m.save()
        ok(http.popleft()) == ('patch', 'api/12/rw_attr', {'field': 19})

    def test_orm_attr_save(self):
        http = make_http()

        class Msg(ORMBase):
            __urls__ = restfull_url_set('api')
            ro_data = attr('api/{id}/ro_attr')
            rw_data = attr('api/{id}/rw_attr', SAME)

        http.responce = {'id': 12, 'field': 'xxx'}
        m = http.load(Msg, 1)
        http.popleft()

        x = m.rw_data
        ok(http.popleft()) == ('get', 'api/12/rw_attr', None)

        x.field = 19
        x.save()
        ok(http.popleft()) == ('patch', 'api/12/rw_attr', {'field': 19})

    def test_diff_in_patch(self):
        http = make_http()

        class Msg(ORMBase):
            __urls__ = restfull_url_set('api')
            ro_data = attr('api/{id}/ro_attr')
            rw_data = attr('api/{id}/rw_attr', SAME)

        http.responce = {'id': 12, 'field': 'xxx'}
        m = http.load(Msg, 1)
        http.popleft()
        x = m.rw_data
        ok(http.popleft()) == ('get', 'api/12/rw_attr', None)

        x.field = 19
        x.save()
        ok(http.popleft()) == ('patch', 'api/12/rw_attr', {'field': 19})

    def test_diff_in_put(self):
        http = make_http()

        class Msg(ORMBase):
            __urls__ = restfull_url_set('api')
            __use_patch__ = False
            ro_data = attr('api/{id}/ro_attr')
            rw_data = attr('api/{id}/rw_attr', SAME)

        http.responce = {'id': 12, 'field': 'xxx'}
        m = http.load(Msg, 1)
        http.popleft()
        m.field = '3434'
        m.save()
        ok(http.popleft()) == ('put', 'api/12', {'field': '3434'})

    def test_no_partial_updates(self):
        pass

    def test_derived_class(self):
        pass

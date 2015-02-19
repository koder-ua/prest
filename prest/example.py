from prest import PRestBase
from prest import GET, POST, DELETE


class MyRestfullAPI(PRestBase):
    list_objs = GET('objects')
    get_obj = GET('objects/{0}')
    del_obj = DELETE('objects/{0}')
    create_obj = POST('objects')
    select_objs = GET('objects/filter')
    objs_by_type = GET('objects/{type}')


def example_func():
    conn = MyRestfullAPI("http://some.api.com/my_api/v2.0")

    print conn.list_objs()

    obj_id = conn.create_obj()['id']
    conn.select_objs(color='read')
    conn.del_obj(obj_id)
    conn.objs_by_type(type='red')

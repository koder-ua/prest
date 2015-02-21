prest documentation
===================

Writing a Python API for a REST service is quite a boring task.
prest is intended to do all of the monkey work for you. Take
a look at an example:

```python
from prest import EasyRestBase, GET, POST, DELETE


class MyRestfullAPI(EasyRestBase):
    list_objs = GET('objects')
    get_obj = GET('objects/{id}')
    del_obj = DELETE('objects/{id}')
    create_obj = POST('objects')
    select_objs = GET('objects/filter')
    objs_by_type = GET('objects/{type}')


conn = MyRestfullAPI("http://some.api.com/my_api/v2.0")

print conn.list_objs()

obj_id = conn.create_obj()['id']
conn.select_objs(color='read')
conn.del_obj(id=obj_id)
conn.objs_by_type(type='red')
```

There are 6 basic functions for HTTP methods:

- GET
- POST
- PUT
- PATCH
- DELETE
- HEAD

Each of them
requires a relative path and returns a function. This 
function, in turn, gets a connection and a set of 
parameters, inserts some of them in the url (if there are placeholders), 
attaches all the rest as GET/POST parameters, and makes 
an HTTP request. The function receives the result, unpacks it and returns the result to the caller.

So you need only one line to make an API func for 
each REST call.
	
In case if result of GET/... calls is assigned to
class method of class inherited from PRestBase
then call gets connection from self. 

Meanwhile you can use it separately:

```python
from prest import GET, Urllib2HTTP_JSON

get_cluster_data = GET('data/{cluster_id}')
conn = Urllib2HTTP_JSON("http://my_api.org")
print get_cluster_data(conn, cluster_id=11)
```

Both Urllib2HTTP_JSON and PRestBase
accepts dictionary of additional headers end echo
parameters. Urllib2HTTP_JSON uses json.dumps and 
json.loads to serialize and deserialize data accordingly.

There also an object-oriented API - please take
a look on test_prest.py. I wrote no documentation 
for it, as it currently breaks 17th rule of python Zen.


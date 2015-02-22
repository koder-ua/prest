prest documentation
===================

Writing a Python API for a REST service is quite a boring task.
prest is intended to do all of the monkey work for you. Take
a look at an example: ::

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

Meanwhile you can use it separately::

	from prest import GET, Urllib2HTTP_JSON

	get_cluster_data = GET('data/{cluster_id}')
	conn = Urllib2HTTP_JSON("http://my_api.org")
	print get_cluster_data(conn, cluster_id=11)


Both Urllib2HTTP_JSON and PRestBase
accepts dictionary of additional headers end echo
parameters. Urllib2HTTP_JSON uses json.dumps and 
json.loads to serialize and deserialize data accordingly.

Parameter dispatching rules::

	func = GET('a/b/{c}/{d}?m={m}')
	func(positional_param, **names_params)

* All named parameters, which match placeholders in url
  would be formatted into url.

* From named parameters, which doesn't match placeholders,
  would be created dictionary, which would be passed as request
  body.

* If not all url placeholder values are provided as named
  parameters all the rest values would be taken from self,
  if api function is inside class.

* If some placeholder cannot be found neither in parameters
  not in self (or no self is provided - in case of standalone
  function). ValueError would be raised.

* At most one positional parameter is allowed. If positional 
  parameter is provided it would be used as entire request body.
  All named parameters in this case should be formatted into url.
  In case if extra named parameters provided - ValueError
  would be raised.

There also an object-oriented API - please take
a look on test_orm.py. I wrote no documentation 
for it, as it currently breaks 17th rule of python Zen.



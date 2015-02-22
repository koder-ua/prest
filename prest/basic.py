import re
import json
import urllib2
import logging
import functools

__all__ = ('Urllib2HTTP', 'Urllib2HTTP_JSON',
           'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD',
           'PRestBase')


def _E(x):
    return x


logger = logging.getLogger('prest')


class Urllib2HTTP(object):
    """
    class for making HTTP requests
    """

    allowed_methods = ('get', 'put', 'post', 'delete', 'patch', 'head')

    def __init__(self, root_url, headers=None, echo=False):
        """
        """
        self.root_url = root_url
        self.headers = headers if headers is not None else {}
        self.echo = echo
        self.unpacker = _E
        self.packer = _E

    def do(self, method, path, params=None):
        url = self.root_url.rstrip('/') + '/' + path.lstrip('/')

        if params is not None:
            data_json = self.packer(params)
        else:
            data_json = None

        if self.echo:
            data_len = 0 if data_json is None else len(data_json)
            msg_templ = "{0} {1} data_len={2}"
            logger.debug(msg_templ.format(method.upper(), url, data_len))

        request = urllib2.Request(url,
                                  data=data_json,
                                  headers=self.headers)
        if data_json is not None:
            request.add_header('Content-Type', 'application/json')

        request.get_method = lambda: method.upper()
        responce = urllib2.urlopen(request)

        if responce.code < 200 or responce.code > 209:
            raise IndexError(url)

        content = responce.read()

        if '' == content:
            return None

        return self.unpacker(content)

    def __getattr__(self, name):
        if name in self.allowed_methods:
            return functools.partial(self.do, name)
        raise AttributeError(name)


class Urllib2HTTP_JSON(Urllib2HTTP):
    def __init__(self, *args, **kwargs):
        super(Urllib2HTTP_JSON, self).__init__(*args, **kwargs)
        self.unpacker = json.loads
        self.packer = json.dumps


format_param_rr = re.compile(r"\{([a-zA-Z_]+)\}")
positional_params_rr = re.compile(r"\{\d+\}")


def http_call(method, url_templ):
    """
    return closure, which would takes parameters and
    makes http calls with given url and method
    """
    inurl_params = set()
    for match in format_param_rr.finditer(url_templ):
        inurl_params.add(match.group(1))

    if positional_params_rr.search(url_templ):
        msg_templ = "Positional parametes aren't allowed in url - {0!r}"
        raise ValueError(msg_templ.format(url_templ))

    def closure(connection, *args, **kwargs):
        if len(args) > 1:
            msg_templ = "No more then one positional" + \
                        " argument might be provided. Got {0!r}"
            raise ValueError(msg_templ.format(args))
        elif len(args) == 1:
            whole_doc = args[0]
        else:
            whole_doc = None

        func = getattr(connection, method)
        inner_obj = kwargs.pop('__inner_obj', None)

        kw_param_names = set(kwargs)
        missing_param_names = inurl_params.difference(kw_param_names)
        data_param_names = kw_param_names.difference(inurl_params)

        if inner_obj is not None:
            # should make a temporary list
            # as missing_param_names changed during iterations
            for name in list(missing_param_names):
                try:
                    kwargs[name] = getattr(inner_obj, name)
                except AttributeError:
                    pass
                else:
                    missing_param_names.remove(name)

        if len(missing_param_names) != 0:
            msg_templ = "Can't found value for parameter(s) {0}"
            raise ValueError(msg_templ.format(",".join(missing_param_names)))

        url = url_templ.format(**kwargs)

        if whole_doc is None:
            whole_doc = {name: kwargs[name] for name in data_param_names}
        elif len(data_param_names) != 0:
            msg_templ = "Extra params {0} passed along with entire doc"
            raise ValueError(msg_templ.format(",".join(data_param_names)))

        return func(url, whole_doc)

    closure.__doc__ = "API call for {0!r} url".format(url_templ)
    closure.__need_connection__ = True
    return closure


GET = functools.partial(http_call, 'get')
POST = functools.partial(http_call, 'post')
PUT = functools.partial(http_call, 'put')
PATCH = functools.partial(http_call, 'patch')
DELETE = functools.partial(http_call, 'delete')
HEAD = functools.partial(http_call, 'head')


def get_func_clusure(attr):
    @functools.wraps(attr)
    def closure(self, *args, **kwargs):
        kwargs['__inner_obj'] = self
        return attr(self.__connection__, *args, **kwargs)
    return closure


class PRestMeta(type):
    def __new__(cls, name, bases, dct):
        new_dct = dct.copy()
        for name, attr in dct.items():
            if getattr(attr, '__need_connection__', False):
                new_dct[name] = get_func_clusure(attr)
        return super(PRestMeta, cls).__new__(cls, name, bases, new_dct)


class PRestBase(object):
    __metaclass__ = PRestMeta

    def __init__(self, conn, **attrs):
        self.__connection__ = conn
        self.__dict__.update(attrs)

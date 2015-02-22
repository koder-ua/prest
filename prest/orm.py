import copy
import pprint
import weakref

from basic import *

__doc__ = "object - REST mapper"

__all__ = ["ORMBase", "attr", "restfull_url_set", "SAME", "OrmHTTPMixIn"]


class OrmHTTPMixIn(object):
    """
    orm mixin. Allows to load and delete objects
    """
    def load(self, cls, oid):
        """
        load instance of class cls with id=oid
        """
        url = cls.__urls__.get.format(id=oid)
        return cls(self, self.get(url))

    def loadall(self, cls):
        """
        load all instances of class cls
        """
        url = cls.__urls__.getall
        return [cls(self, obj_data) for obj_data in self.get(url)]

    def delete(self, obj_or_cls, oid=None):
        if oid is None:
            oid = obj_or_cls.id
        url = obj_or_cls.__urls__.delete.format(id=oid)
        self.delete(url, None)


class Engine(Urllib2HTTP, OrmHTTPMixIn):
    pass


class Urls(object):
    def __init__(self, get=None, getall=None, create=None, update=None,
                 delete=None):

        self.get = get
        self.getall = getall
        self.create = create
        self.update = update
        self.delete = delete


def restfull_url_set(root_url, methods="gacud"):
    root_url_list = [i for i in root_url.split('/') if i != ""]
    if "{id}" not in root_url_list:
        root_url_list.append("{id}")

    root_url_no_id = "/".join(i for i in root_url_list if i != "{id}")
    root_url_upd = "/".join(root_url_list)

    getall_url = root_url_no_id if 'a' in methods else None
    create_url = root_url_no_id if 'c' in methods else None
    get_url = root_url_upd if 'g' in methods else None
    update_url = root_url_upd if 'u' in methods else None
    delete_url = root_url_upd if 'a' in methods else None

    return Urls(get=get_url,
                getall=getall_url,
                create=create_url,
                update=update_url,
                delete=delete_url)


def make_rest_patch(old, new):
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    patch = {new_key: new[new_key] for new_key in new_keys - old_keys}

    for same_key in old_keys & new_keys:
        if old[same_key] != new[same_key]:
            patch[same_key] = new[same_key]

    assert set() == (old_keys - new_keys)
    return patch


class Updater(object):
    def __init__(self, urls, data, transport=None, use_patch=True,
                 partial_updates=True):
        self.urls = urls
        self.use_patch = use_patch
        self.partial_updates = partial_updates
        self.transport = None
        self.set_transport(transport)
        if self.partial_updates and isinstance(data, dict):
            self.old = copy.deepcopy(data)
        else:
            self.old = None

    def set_transport(self, transport):
        if transport is None:
            self.transport = None
        else:
            self.transport = transport

    def save(self, oid, new):
        data_updated = False
        if oid is None:
            res = self.transport.post(self.urls.create, new)
            data_updated = True
            if isinstance(res, dict):
                oid = res.get('id')

        elif self.partial_updates \
                and isinstance(new, dict) \
                and self.old is not None:

            url = self.urls.update.format(id=oid)
            try:
                diff = make_rest_patch(self.old, new)
            except (ValueError, AssertionError):
                self.transport.put(url, new)
                data_updated = True
            else:
                if diff != {}:
                    data_updated = True
                    if self.use_patch:
                        self.transport.patch(url, diff)
                    else:
                        self.transport.put(url, diff)
        else:
            self.transport.put(url, new)
            data_updated = True

        if self.partial_updates and data_updated:
            self.old = copy.deepcopy(new)

        return oid


class ORMBase(PRestBase):
    __urls__ = Urls(None, None, None, None, None)
    __updater_cls__ = Updater
    __use_patch__ = True
    __partial_updates__ = True

    def __init__(self, transport=None, params=None):
        super(ORMBase, self).__init__(transport)
        upd_params = params.copy()
        if 'id' in upd_params:
            del upd_params['id']

        pu = self.__partial_updates__
        self.__updater__ = self.__updater_cls__(self.__urls__,
                                                upd_params,
                                                transport=transport,
                                                use_patch=self.__use_patch__,
                                                partial_updates=pu)
        self.__children__ = []

        if params is not None:
            assert not any(hasattr(self, k) for k in params)
            self.__dict__.update(params)

        if not hasattr(self, 'id'):
            self.id = None

    def __clean_data__(self):
        dct = self.__dict__.copy()

        del dct['__children__']
        del dct['__updater__']
        del dct['__connection__']
        del dct['id']

        return dct

    def __register_child__(self, child):
        self.__children__.append(child)

    def __unregister_child__(self, child):
        self.__children__.remove(child)

    def save(self):
        self.id = self.__updater__.save(self.id, self.__clean_data__())

        for child in self.__children__:
            child.save()

    def set_transport(self, transport):
        self.__updater__.set_transport(transport)

    def __get_transport__(self):
        return self.__updater__.transport

    @classmethod
    def make(cls, transport, **params):
        return cls(transport, params)

    def __str__(self):
        return pprint.pformat(self.__clean_data__())

    def __iter__(self):
        return iter(self.__clean_data__())

    def items(self):
        return self.__clean_data__().items()

    def keys(self):
        return self.__clean_data__().keys()

    def values(self):
        return self.__clean_data__().values()

    def __getitem__(self, idx):
        return self.__clean_data__()[idx]

    def __setitem__(self, idx, val):
        self.__dict__[idx] = val


class SAME(object):
    pass


class DictAttrValue(ORMBase):
    def __init__(self, parent, params):
        transport = parent.__get_transport__()
        super(DictAttrValue, self).__init__(transport, params)
        self.__par_wref__ = weakref.ref(parent)

    def save(self):
        self.__updater__.save(self.__par_wref__().id, self.__clean_data__())

    def __clean_data__(self):
        dct = super(DictAttrValue, self).__clean_data__()
        del dct['__par_wref__']
        return dct


class ListAttrValue(object):
    def __init__(self, parent, data, save_url):
        self.par_wref = weakref.ref(parent)
        self.save_url = save_url
        self.data = data

    def save(self):
        if self.save_url is not None:
            par = self.par_wref()
            url = self.save_url.format(id=par.id)
            par.__get_transport__().put(url, self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

    def __setitem__(self, idx, val):
        self.data[idx] = val

    def __len__(self):
        return len(self.data)

    def __add__(self, x):
        return self.data + x

    def __iadd__(self, x):
        return x + self.data

    def __delitem__(self, idx):
        del self.data[idx]

    def insert(self, idx, val):
        self.data.insert(idx, val)

    def append(self, val):
        self.data.append(val)

    def extend(self, val):
        self.data.extend(val)

    def __str__(self):
        return "[{}]".format(map(str, self))

    def __repr__(self):
        return str(self)


def make_attr(raw_value, urls, parent, use_patch, partial_updates):
    if isinstance(raw_value, list):
        return ListAttrValue(parent, raw_value, urls.update)
    if isinstance(raw_value, dict):
        class InnerAttr(DictAttrValue):
            __urls__ = urls
            __use_patch__ = use_patch
            __partial_updates__ = partial_updates

        return InnerAttr(parent, raw_value)

    tname = type(raw_value).__name__
    raise ValueError("Don't know how to wrap value of type {0}".format(tname))


class RestAttr(object):
    def __init__(self, urls, use_patch, partial_updates, cls=None):
        self.dirty = False
        self.urls = urls
        self.use_patch = use_patch
        self.partial_updates = partial_updates
        self.cls = cls

    def __get__(self, obj, owner):
        try:
            return self.data
        except AttributeError:
            url = self.urls.get.format(id=obj.id)
            raw_data = obj.__get_transport__().get(url)

            if self.cls is not None:
                func = self.cls
            else:
                func = make_attr

            self.data = func(raw_data,
                             self.urls,
                             obj,
                             self.use_patch,
                             self.partial_updates)

            if self.urls.update is not None:
                obj.__register_child__(self.data)

            return self.data

    def __set__(self, obj, value):
        if self.urls.update is None:
            raise ValueError("Can't set to readonly field")
        try:
            self.data  # check attr exists
            obj.__unregister_child__(self.data)
        except AttributeError:
            pass

        self.data = make_attr(value,
                              self.urls,
                              obj,
                              self.use_patch,
                              self.partial_updates)

        obj.__register_child__(self.data)

    def __delete__(self, obj):
        if self.urls.delete is None:
            raise ValueError("Can't delete this field")
        raise NotImplementedError("del for REST.attr")


def attr(get_url=None, update_url=None, delete_url=None, use_patch=True,
         partial_updates=True):
    if update_url is SAME:
        update_url = get_url

    if delete_url is SAME:
        delete_url = get_url

    urls = Urls(get=get_url, update=update_url, delete=delete_url)
    return RestAttr(urls, use_patch, partial_updates)


def mattr(cls, get_url=None,
          update_url=None,
          delete_url=None,
          use_patch=True,
          partial_updates=True):

    if update_url is SAME:
        update_url = get_url

    if delete_url is SAME:
        delete_url = get_url

    urls = Urls(get=get_url, update=update_url, delete=delete_url)
    return RestAttr(urls, use_patch, partial_updates, cls=cls)

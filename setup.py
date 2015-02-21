#!/usr/bin/env python
import os
from setuptools import setup


PROJECT = 'prest'
VERSION = '0.2.5'
URL = 'https://github.com/koder-ua/prest'
AUTHOR = 'K.Danilov aka koder'
AUTHOR_EMAIL = 'koder.mail@gmail.com'
DESC = "This module makes writing client API for REST " + \
       "services as easy as GET('my_api/{some_param}')"


def read_file(file_name):
    file_path = os.path.join(
        os.path.dirname(__file__),
        file_name
        )
    return open(file_path).read()

setup(name=PROJECT,
      version=VERSION,
      description=DESC,
      url=URL,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license='LGPL',
      packages=[PROJECT],
      zip_safe=False,
      long_description=read_file("README.rst"))

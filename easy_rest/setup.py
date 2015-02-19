#!/usr/bin/env python
import os
from setuptools import setup


PROJECT = 'easy_rest'
VERSION = '0.1'
URL = 'https://github.com/koder-ua/easy_rest'
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
      version='0.1',
      description=DESC,
      url='https://github.com/koder-ua/easy_rest',
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license='LGPL',
      packages=[PROJECT],
      zip_safe=False)

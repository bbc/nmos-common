#!/usr/bin/python
#
# Copyright 2017 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from setuptools import setup
import os


def is_package(path):
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
        )


def find_packages(path, base=""):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package(dir):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages


packages = find_packages(".")
package_names = packages.keys()

packages_required = [
    "gevent>=1.2.2",
    "greenlet>=0.4.13",
    "gevent-websocket>=0.9.3",
    "six>=1.10.0",
    "flask==0.10.1",
    "jinja2>=2.7.2",
    "werkzeug>=0.9.4",
    "itsdangerous>=0.24",
    "socketio-client>=0.5.3",
    "flask-sockets==0.1",
    "pyzmq>=15.2.0",
    "pygments>=1.6",
    "python-dateutil>=2.4.2,<2.7.0",
    "flask-oauthlib==0.9.1",
    "ws4py>=0.3.2",
    "requests>=2.6",
    "jsonschema>=2.3.0",
    "netifaces>=0.10.6",
    "websocket-client>=0.18.0",
    "pybonjour==1.1.1"
]

# The following are included only as the package fails to download from pip
deps_required = [
    "https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/pybonjour/pybonjour-1.1.1.tar.gz#egg=pybonjour-1.1.1"
]


setup(name="nmoscommon",
      version="0.4.1",
      description="nmos python utilities",
      url='www.nmos.tv',
      author='Peter Brightwell',
      author_email='peter.brightwell@bbc.co.uk',
      license='Apache 2',
      packages=package_names,
      package_dir=packages,
      install_requires=packages_required,
      dependency_links=deps_required,
      scripts=[],
      data_files=[
          ("/etc/nmoscommon", ["data/config.json"])
      ],
      long_description="""\
Implementation of the nmos python utilities"""
      )

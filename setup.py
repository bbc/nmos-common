#!/usr/bin/python
#

from distutils.core import setup
from distutils.version import LooseVersion
import os
import sys

def check_packages(packages):
    failure = False
    for python_package, package_details in packages:
        try:
            __import__(python_package)
        except ImportError as err:
            failure = True
            print "Cannot find", python_package,
            print "you need to install :", package_details

    return not failure

def check_dependencies(packages):
    failure = False
    for python_package, dependency_filename, dependency_url in packages:
        try:
            __import__(python_package)
        except ImportError as err:
            failure = True
            print
            print "Cannot find", python_package,
            print "you need to install :", dependency_filename
            print "... originally retrieved from", dependency_url

    return not failure

def is_package(path):
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
        )

def find_packages(path, base="" ):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package( dir ):
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
    "gevent=1.0.2",
    "greenlet=0.4.2",
    "gevent-websocket=0.9.3",
    "six=1.10.0",
    "flask=0.10.1",
    "jinja=22.7.2",
    "werkzeug=0.9.4",
    "itsdangerous=0.24",
    "socketio-client=0.5.3",
    "flask-sockets=0.1",
    "pyzmq",
    "pygments=1.6",
    "python-dateutil",
    "flask-oauthlib=0.9.1",
    "ws4py=0.3.2",
    "requests=2.2.1",
    "jsonschema=2.3.0",
    "netifaces"
]

deps_required = []

setup(name = "nmoscommon",
      version = "0.1.0",
      description = "nmos python utilities",
      url='www.nmos.tv',
      author='Peter Brightell',
      author_email='peter.brightwell@bbc.co.uk',
      license='Apache 2',
      packages = package_names,
      package_dir = packages,
      install_requires = packages_required,
      scripts = [
                ],
      data_files=[
                 ],
      long_description = """
Implementation of the nmos python utilities
"""
      )

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
import setuptools
import os
import sys
import json
from setuptools.command.develop import develop
from setuptools.command.install import install


def create_default_conf():
    fname = "/etc/nmoscommon/config.json"
    if os.path.isfile(fname):
        return

    # Defaults defined in nmoscommonconfig.py
    defaultData = {
        "priority": 0,
        "https_mode": "disabled",
        "prefer_ipv6": False,
        "prefer_hostnames": False,
        "node_hostname": None,
        "fix_proxy": "disabled",
        "logging": {
            "level": "DEBUG",
            "fileLocation": "/var/log/nmos.log",
            "output": [
                "file",
                "stdout"
            ]
        },
        "nodefacade": {
            "NODE_REGVERSION": "v1.2"
        },
        "oauth_mode": False,
        "dns_discover": True,
        "mdns_discover": True,
        "interfaces": []
    }

    try:
        try:
            os.makedirs(os.path.dirname(fname))
        except OSError as e:
            if e.errno != os.errno.EEXIST:
                raise
            pass

        with open(fname, 'w') as outfile:
            json.dump(defaultData,
                      outfile,
                      sort_keys=True,
                      indent=4,
                      separators=(",", ": "))
    except OSError as e:
        if e.errno != os.errno.EACCES:
            raise
        pass
        # Default config couldn't be created.
        # Code will fallback to hardcoded defaults.
        # This should only happen with un-priviladged installs


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        create_default_conf()


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        create_default_conf()


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

# REMEMBER: If this list is updated, please also update stdeb.cfg
packages_required = [
    "gevent>=1.2.2",
    "greenlet>=0.4.13",
    "gevent-websocket>=0.9.3",
    "six>=1.10.0",
    "flask>=0.10.1",
    "jinja2>=2.7.2",
    "werkzeug>=0.14.1",
    "itsdangerous>=0.24",
    "socketio-client>=0.5.3",
    "flask-sockets>=0.1",
    "pyzmq>=15.2.0",
    "pygments>=1.6",
    "python-dateutil>=2.4.2",
    "oauthlib<3.0.0",
    "requests-oauthlib<1.2.0",
    "flask-oauthlib>=0.9.1",
    "ws4py>=0.3.2",
    "requests>=2.6",
    "jsonschema>=2.3.0",
    "netifaces>=0.10.6",
    "websocket-client>=0.18.0",
    "ujson>=1.33",
    "mediatimestamp>=1.0.1",
    "mediajson>=1.0.0",
    "authlib>=0.10",
    "pyopenssl",
    "dnspython>=1.12.0",
    "zeroconf-monkey>=0.1.0"
]

# Check if setuptools is recent enough to recognise python_version syntax
# Pybonjour is only available for Python 2
# wsaccel doesn't work with python 3.6
if int(setuptools.__version__.split(".", 1)[0]) < 18:
    # Check python version using legacy mechanism
    if sys.version_info[0:2] < (3, 0):
        packages_required.extend([
            "zeroconf<=0.19.1"
        ])  # Version locked to preserve Python 2 compatibility
    else:
        packages_required.extend([
            "zeroconf>=0.21.0"
        ])

    if sys.version_info[0:2] < (3, 6):
        packages_required.extend([
            'wsaccel>=0.6.2',
        ])
else:
    packages_required.extend([
        "zeroconf==0.19.1;python_version<'3.0'",
        "zeroconf>=0.21.0;python_version>='3.0'",
        'wsaccel>=0.6.2;python_version<"3.6"'
    ])

deps_required = []


setup(
    name="nmoscommon",
    version="0.19.9",
    description="Common components for the BBC's NMOS implementations",
    url='https://github.com/bbc/nmos-common',
    author='Peter Brightwell',
    author_email='peter.brightwell@bbc.co.uk',
    license='Apache 2',
    packages=package_names,
    package_dir=packages,
    install_requires=packages_required,
    dependency_links=deps_required,
    scripts=[],
    data_files=[],
    long_description="Common components for the BBC's NMOS implementations",
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    }
)

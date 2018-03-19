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

from six import PY2
from six.moves import reload_module

import unittest
import mock

from six.moves.urllib.parse import urlparse as urlparse_urlparse

import nmoscommon.webapi

if PY2:
    BUILTINS = "__builtin__"
else:
    BUILTINS = "builtins"

#import urlparse.urlparse
#import urllib.request
#import urllib.parse

orig_import = __import__
mock_imports = {}
def import_mock(magic_names, cursed_names):
    """An explanation of how this import gubbins works:

    * The __import__ function is the underlying python function called by import statements
    * Here I save the existing __import__ function and then use mock.patch to replace it with a custom function
    * The custom function normally passes through to the default __import__ function, but when you try to import a specific module
      (in this case "urllib2") it instead either raises an ImportError exception or passes back a mock masquerading as
      the module.
    * The use of this is because the module under test starts by importing urllib2 and then behaves differently depending on
      whether that raises an exception. By substituing a mock for the module we can force it to succeed even on systems where urllib2 is not
      installed, or by raising the exception we can force the import to fail even on systems where the module is installed. This allows us to 
      test both sets of behaviour from the module."""
    def __inner(name, *args, **kwargs):
        if name in magic_names:
            if name not in mock_imports:
                mock_imports[name] = mock.MagicMock(name=name)
            return mock_imports[name]
        elif name in cursed_names:
            raise ImportError
        else:
            return orig_import(name, *args, **kwargs)
    return __inner

class TestImport(unittest.TestCase):
    def test_import_with_urllib2(self):
        with mock.patch(BUILTINS + '.__import__', import_mock(['urllib2', ], [])):
            reload_module(nmoscommon.webapi)
            from nmoscommon.webapi import http, urlparse
            self.assertEqual(http, mock_imports['urllib2'])
            self.assertEqual(urlparse, urlparse_urlparse)

    def test_import_without_urllib2(self):
        with mock.patch(BUILTINS + '.__import__', import_mock(['urllib', 'urllib.parse' ], ['urllib2',])):
            reload_module(nmoscommon.webapi)
            from nmoscommon.webapi import http, urlparse
            self.assertEqual(http, mock_imports['urllib'].request)
            self.assertEqual(urlparse, mock_imports['urllib.parse'].urlparse)

    def test_getlocalip_for_host(self):
        with mock.patch('nmoscommon.utils.getLocalIP', return_value=mock.sentinel.localip):
            reload_module(nmoscommon.webapi)
            from nmoscommon.webapi import HOST
            self.assertEqual(HOST, mock.sentinel.localip)

    def test_getlocalip_for_host_retries_on_failure(self):
        with mock.patch('time.sleep'):
            with mock.patch('nmoscommon.utils.getLocalIP', side_effect=[ Exception, mock.sentinel.localip ]):
                reload_module(nmoscommon.webapi)
                from nmoscommon.webapi import HOST
                self.assertEqual(HOST, mock.sentinel.localip)

    def test_getlocalip_for_host_gives_up_after_six_retries(self):
        with mock.patch('time.sleep'):
            with mock.patch('nmoscommon.utils.getLocalIP', side_effect=[ Exception, Exception, Exception, Exception, Exception, Exception, Exception, mock.sentinel.localip ]):
                with self.assertRaises(OSError):
                    reload_module(nmoscommon.webapi)
                    from nmoscommon.webapi import HOST

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
import traceback
import json

import nmoscommon
import nmoscommon.nmoscommonconfig

if PY2:
    BUILTINS = "__builtin__"
else:
    BUILTINS = "builtins"

class TestNMOSCommonConfig(unittest.TestCase):
    def test_import(self):
        test_data = { "foo" : "bar",
                      "baz" : [ "potato", ] }
        with mock.patch('os.path.isfile', return_value=True) as isfile:
            with mock.patch(BUILTINS + '.open', create=True) as _open:
                _open.return_value.read.return_value = json.dumps(test_data)
                reload_module(nmoscommon.nmoscommonconfig)
                from nmoscommon.nmoscommonconfig import config
                isfile.assert_called_with('/etc/nmoscommon/config.json')
                for test_key in test_data.keys():
                    self.assertIn(test_key, config)
                    self.assertEqual(test_data[test_key], config[test_key])

    def test_import_exception(self):
        test_data = { "foo" : "bar",
                      "baz" : [ "potato", ] }
        with mock.patch('os.path.isfile', return_value=True) as isfile:
            with mock.patch(BUILTINS + '.open', create=True, side_effect=Exception) as _open:
                reload_module(nmoscommon.nmoscommonconfig)
                from nmoscommon.nmoscommonconfig import config, config_defaults
                isfile.assert_called_with('/etc/nmoscommon/config.json')
                self.assertEqual(config, config_defaults)

    def test_import_when_no_file(self):
        test_data = { "foo" : "bar",
                      "baz" : [ "potato", ] }
        with mock.patch('os.path.isfile', return_value=False) as isfile:
            with mock.patch(BUILTINS + '.open', create=True) as _open:
                reload_module(nmoscommon.nmoscommonconfig)
                from nmoscommon.nmoscommonconfig import config, config_defaults
                isfile.assert_called_with('/etc/nmoscommon/config.json')
                self.assertEqual(config, config_defaults)

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

import unittest
import mock
import traceback
import json

import nmoscommon
import nmoscommon.nmoscommonconfig

class TestNMOSCommonConfig(unittest.TestCase):
    def test_import(self):
        test_data = { "foo" : "bar",
                      "baz" : [ "potato", ] }
        with mock.patch('os.path.isfile', return_value=True) as isfile:
            with mock.patch('__builtin__.open', create=True) as _open:
                _open.return_value.read.return_value = json.dumps(test_data)
                reload(nmoscommon.nmoscommonconfig)
                from nmoscommon.nmoscommonconfig import config
                isfile.assert_called_with('/etc/nmoscommon/config.json')
                self.assertEqual(config, test_data)

    def test_import_exception(self):
        test_data = { "foo" : "bar",
                      "baz" : [ "potato", ] }
        with mock.patch('os.path.isfile', return_value=True) as isfile:
            with mock.patch('__builtin__.open', create=True, side_effect=Exception) as _open:
                reload(nmoscommon.nmoscommonconfig)
                from nmoscommon.nmoscommonconfig import config
                isfile.assert_called_with('/etc/nmoscommon/config.json')
                self.assertEqual(config, {})

    def test_import_when_no_file(self):
        test_data = { "foo" : "bar",
                      "baz" : [ "potato", ] }
        with mock.patch('os.path.isfile', return_value=False) as isfile:
            with mock.patch('__builtin__.open', create=True) as _open:
                reload(nmoscommon.nmoscommonconfig)
                from nmoscommon.nmoscommonconfig import config
                isfile.assert_called_with('/etc/nmoscommon/config.json')
                self.assertEqual(config, {})

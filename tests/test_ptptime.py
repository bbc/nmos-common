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
import time

import nmoscommon
from nmoscommon.ptptime import *
import mock

if PY2:
    BUILTINS = "__builtin__"
else:
    BUILTINS = "builtins"

orig_import = __import__

def import_mock(magic_name, allow):
    def __inner(name, *args):
        if name == magic_name:
            if allow:
                return mock.MagicMock()
            else:
                raise ImportError
        else:
            return orig_import(name, *args)
    return __inner

class PTPTest(unittest.TestCase):

    def test_import_noerror(self):
        with mock.patch(BUILTINS + '.__import__', side_effect=import_mock("ipppython.ptptime",True)):
            reload_module(nmoscommon.ptptime)
            from nmoscommon.ptptime import IPP_PYTHON
            self.assertTrue(IPP_PYTHON)
    
    def test_import_error(self):
        with mock.patch(BUILTINS + '.__import__', side_effect=import_mock("ipppython.ptptime",False)):
            reload_module(nmoscommon.ptptime)
            from nmoscommon.ptptime import IPP_PYTHON
            self.assertFalse(IPP_PYTHON)

    def test_ptp_detail(self):
        """Testing the fallback when IPP_PYTHON doesn't load"""
        with mock.patch(BUILTINS + '.__import__', side_effect=import_mock("ipppython.ptptime",False)):
            reload_module(nmoscommon.ptptime)
            from nmoscommon.ptptime import ptp_detail
            rv = ptp_detail()
            self.assertEqual(2, len(rv))
            self.assertTrue(isinstance(rv[0], int))
            self.assertTrue(isinstance(rv[1], int))

    def test_fallback(self):
        with mock.patch('nmoscommon.timestamp.Timestamp.get_time') as get_time:
            with mock.patch(BUILTINS + '.__import__', side_effect=import_mock("ipppython.ptptime",False)):
                tval = 23*1e9 + 17
                get_time.return_value.to_nanosec.return_value = tval
                reload_module(nmoscommon.ptptime)
                from nmoscommon.ptptime import ptp_time
                ts = ptp_time()
                get_time.assert_called_once_with()
                self.assertEqual(ts, tval/1e9)

import unittest
import time

import nmoscommon
from nmoscommon.ptptime import *
import mock

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
        with mock.patch('__builtin__.__import__', side_effect=import_mock("ipppython.ptptime",True)):
            reload(nmoscommon.ptptime)
            from nmoscommon.ptptime import IPP_PYTHON
            self.assertTrue(IPP_PYTHON)
    
    def test_import_error(self):
        with mock.patch('__builtin__.__import__', side_effect=import_mock("ipppython.ptptime",False)):
            reload(nmoscommon.ptptime)
            from nmoscommon.ptptime import IPP_PYTHON
            self.assertFalse(IPP_PYTHON)

    def test_ptp_detail(self):
        """Testing the fallback when IPP_PYTHON doesn't load"""
        with mock.patch('__builtin__.__import__', side_effect=import_mock("ipppython.ptptime",False)):
            reload(nmoscommon.ptptime)
            from nmoscommon.ptptime import ptp_detail
            rv = ptp_detail()
            self.assertEqual(2, len(rv))
            self.assertTrue(isinstance(rv[0], int))
            self.assertTrue(isinstance(rv[1], int))

    def test_fallback(self):
        with mock.patch('nmoscommon.ptptime.Timestamp.get_time') as get_time:
            with mock.patch('__builtin__.__import__', side_effect=import_mock("ipppython.ptptime",False)):
                tval = 23*1e9 + 17
                get_time.return_value.to_nanosec.return_value = tval
                reload(nmoscommon.ptptime)
                from nmoscommon.ptptime import ptp_time
                ts = ptp_time()
                get_time.assert_called_once_with()
                self.assertEqual(ts, tval/1e9)

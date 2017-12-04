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
import dbus
from nmoscommon.mdns.bonjour import *
import pybonjour
import traceback

class ExitTestNormally(Exception):
    pass

def catch_and_return_default(f):
    try:
        f()
    except ExitTestNormally as e:
        pass
    return mock.DEFAULT

class TestMDNSEngine(unittest.TestCase):

    def test_init(self):
        UUT = MDNSEngine()

    @mock.patch('select.select', return_value=[ [], [], [] ])
    @mock.patch('time.sleep', side_effect=ExitTestNormally)
    @mock.patch('gevent.spawn', side_effect=catch_and_return_default)
    def test_start(self, spawn, sleep, select):
        UUT = MDNSEngine()

        UUT.start()
        select.assert_not_called()
        sleep.assert_called_once_with(mock.ANY)

    @mock.patch('pybonjour.DNSServiceProcessResult')
    @mock.patch('pybonjour.DNSServiceRegister')
    @mock.patch('select.select')
    @mock.patch('time.sleep', side_effect=ExitTestNormally)
    @mock.patch('gevent.spawn')
    def test_register(self, spawn, sleep, select, dnsserviceregister, dnsserviceprocessresult):
        txtRecord={ 'name' : "Test Text Record",
                    'foo' : 'bar' }
        callback = mock.MagicMock(name="callback")

        select.side_effect = [ [ [ dnsserviceregister.return_value, ], [], [] ],
                               ExitTestNormally ]

        UUT = MDNSEngine()

        UUT.start()
        run = spawn.call_args[0][0]

        self.assertEqual(dnsserviceregister.return_value, UUT.register(mock.sentinel.name, mock.sentinel.regtype, mock.sentinel.port, txtRecord=txtRecord, callback=callback))
        dnsserviceregister.assert_called_once_with(name=mock.sentinel.name,
                                                   regtype=mock.sentinel.regtype,
                                                   port=mock.sentinel.port,
                                                   callBack=callback,
                                                   txtRecord=mock.ANY)
        # pybonjour.TXTRecord doesn't correctly define equality comparisons, this will check it
        self.assertEqual(str(dnsserviceregister.call_args[1]["txtRecord"]), str(pybonjour.TXTRecord(txtRecord)))

        try:
            run()
        except ExitTestNormally:
            pass
        except:
            self.fail(msg="Run raised unexpected error: %s" % (traceback.print_exc(),))

        dnsserviceprocessresult.assert_called_once_with(dnsserviceregister.return_value)

    @mock.patch('pybonjour.DNSServiceProcessResult')
    @mock.patch('pybonjour.DNSServiceRegister')
    @mock.patch('select.select')
    @mock.patch('time.sleep', side_effect=ExitTestNormally)
    @mock.patch('gevent.spawn')
    def test_register_without_txtrecord(self, spawn, sleep, select, dnsserviceregister, dnsserviceprocessresult):
        callback = mock.MagicMock(name="callback")

        select.side_effect = [ [ [ dnsserviceregister.return_value, ], [], [] ],
                               ExitTestNormally ]

        UUT = MDNSEngine()

        UUT.start()
        run = spawn.call_args[0][0]

        self.assertEqual(dnsserviceregister.return_value, UUT.register(mock.sentinel.name, mock.sentinel.regtype, mock.sentinel.port, callback=callback))
        dnsserviceregister.assert_called_once_with(name=mock.sentinel.name,
                                                   regtype=mock.sentinel.regtype,
                                                   port=mock.sentinel.port,
                                                   callBack=callback,
                                                   txtRecord=mock.ANY)
        # pybonjour.TXTRecord doesn't correctly define equality comparisons, this will check it
        self.assertEqual(str(dnsserviceregister.call_args[1]["txtRecord"]), str(pybonjour.TXTRecord({})))

        try:
            run()
        except ExitTestNormally:
            pass
        except:
            self.fail(msg="Run raised unexpected error: %s" % (traceback.print_exc(),))

        dnsserviceprocessresult.assert_called_once_with(dnsserviceregister.return_value)

    @mock.patch('pybonjour.DNSServiceUpdateRecord')
    @mock.patch('gevent.spawn')
    def test_update_does_nothing_on_its_own(self, spawn, dnsserviceupdaterecord):
        callback = mock.MagicMock(name="callback")

        UUT = MDNSEngine()

        UUT.start()

        self.assertFalse(UUT.update(mock.sentinel.name, mock.sentinel.regtype))
        dnsserviceupdaterecord.assert_not_called()

    @mock.patch('pybonjour.DNSServiceProcessResult')
    @mock.patch('pybonjour.DNSServiceRegister')
    @mock.patch('pybonjour.DNSServiceUpdateRecord')
    @mock.patch('select.select')
    @mock.patch('time.sleep', side_effect=ExitTestNormally)
    @mock.patch('gevent.spawn')
    def test_update_updates(self, spawn, sleep, select, dnsserviceupdaterecord, dnsserviceregister, dnsserviceprocessresult):
        txtRecord={ 'name' : "Test Text Record",
                    'foo' : 'bar' }
        newTxtRecord = { 'name' : "Test Text Record",
                         'foo' : 'baz' }
        callback = mock.MagicMock(name="callback")

        select.side_effect = [ [ [ dnsserviceregister.return_value, ], [], [] ],
                               ExitTestNormally ]

        UUT = MDNSEngine()

        UUT.start()
        run = spawn.call_args[0][0]

        self.assertEqual(dnsserviceregister.return_value, UUT.register(mock.sentinel.name, mock.sentinel.regtype, mock.sentinel.port, txtRecord=txtRecord, callback=callback))
        dnsserviceregister.assert_called_once_with(name=mock.sentinel.name,
                                                   regtype=mock.sentinel.regtype,
                                                   port=mock.sentinel.port,
                                                   callBack=callback,
                                                   txtRecord=mock.ANY)
        # pybonjour.TXTRecord doesn't correctly define equality comparisons, this will check it
        self.assertEqual(str(dnsserviceregister.call_args[1]["txtRecord"]), str(pybonjour.TXTRecord(txtRecord)))

        try:
            run()
        except ExitTestNormally:
            pass
        except:
            self.fail(msg="Run raised unexpected error: %s" % (traceback.print_exc(),))

        dnsserviceprocessresult.assert_called_once_with(dnsserviceregister.return_value)

        self.assertTrue(UUT.update(mock.sentinel.name, mock.sentinel.regtype, txtRecord=newTxtRecord))
        dnsserviceupdaterecord.assert_called_once_with(dnsserviceregister.return_value, None, 0, mock.ANY, 0)
        self.assertEqual(str(dnsserviceupdaterecord.call_args[0][3]), str(pybonjour.TXTRecord(newTxtRecord)))

    @mock.patch('pybonjour.DNSServiceProcessResult')
    @mock.patch('pybonjour.DNSServiceRegister')
    @mock.patch('pybonjour.DNSServiceUpdateRecord')
    @mock.patch('select.select')
    @mock.patch('time.sleep', side_effect=ExitTestNormally)
    @mock.patch('gevent.spawn')
    def test_update_can_remove_txt_record(self, spawn, sleep, select, dnsserviceupdaterecord, dnsserviceregister, dnsserviceprocessresult):
        txtRecord={ 'name' : "Test Text Record",
                    'foo' : 'bar' }
        callback = mock.MagicMock(name="callback")

        select.side_effect = [ [ [ dnsserviceregister.return_value, ], [], [] ],
                               ExitTestNormally ]

        UUT = MDNSEngine()

        UUT.start()
        run = spawn.call_args[0][0]

        self.assertEqual(dnsserviceregister.return_value, UUT.register(mock.sentinel.name, mock.sentinel.regtype, mock.sentinel.port, txtRecord=txtRecord, callback=callback))
        dnsserviceregister.assert_called_once_with(name=mock.sentinel.name,
                                                   regtype=mock.sentinel.regtype,
                                                   port=mock.sentinel.port,
                                                   callBack=callback,
                                                   txtRecord=mock.ANY)
        # pybonjour.TXTRecord doesn't correctly define equality comparisons, this will check it
        self.assertEqual(str(dnsserviceregister.call_args[1]["txtRecord"]), str(pybonjour.TXTRecord(txtRecord)))

        try:
            run()
        except ExitTestNormally:
            pass
        except:
            self.fail(msg="Run raised unexpected error: %s" % (traceback.print_exc(),))

        dnsserviceprocessresult.assert_called_once_with(dnsserviceregister.return_value)

        self.assertTrue(UUT.update(mock.sentinel.name, mock.sentinel.regtype))
        dnsserviceupdaterecord.assert_called_once_with(dnsserviceregister.return_value, None, 0, mock.ANY, 0)
        self.assertEqual(str(dnsserviceupdaterecord.call_args[0][3]), str(pybonjour.TXTRecord({})))

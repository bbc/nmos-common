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
from nmoscommon.mdns.bonjour import *
import traceback

try:
    import pybonjour
except:
    pass
else:

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

        @mock.patch('gevent.spawn')
        def test_start_restarts_if_necessary(self, spawn):
            UUT = MDNSEngine()
            UUT.start()
            spawn.assert_called_once_with(mock.ANY)
            spawn.return_value.assert_not_called()
            spawn.reset_mock()
            spawn.return_value.reset_mock()
            UUT.start()
            spawn.assert_called_once_with(mock.ANY)
            spawn.return_value.kill.assert_called_once_with()

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
        def test_register_without_callback(self, spawn, sleep, select, dnsserviceregister, dnsserviceprocessresult):
            txtRecord={ 'name' : "Test Text Record",
                        'foo' : 'bar' }

            select.side_effect = [ [ [ dnsserviceregister.return_value, ], [], [] ],
                                   ExitTestNormally ]

            UUT = MDNSEngine()

            UUT.start()
            run = spawn.call_args[0][0]

            self.assertEqual(dnsserviceregister.return_value, UUT.register(mock.sentinel.name, mock.sentinel.regtype, mock.sentinel.port, txtRecord=txtRecord))
            dnsserviceregister.assert_called_once_with(name=mock.sentinel.name,
                                                       regtype=mock.sentinel.regtype,
                                                       port=mock.sentinel.port,
                                                       callBack=mock.ANY,
                                                       txtRecord=mock.ANY)
            # pybonjour.TXTRecord doesn't correctly define equality comparisons, this will check it
            self.assertEqual(str(dnsserviceregister.call_args[1]["txtRecord"]), str(pybonjour.TXTRecord(txtRecord)))
            callback = dnsserviceregister.call_args[1]["callBack"]
            try:
                callback()
            except:
                self.fail(msg="default callback supplied by module throws exception")

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

        @mock.patch('pybonjour.DNSServiceProcessResult')
        @mock.patch('pybonjour.DNSServiceRegister')
        @mock.patch('select.select')
        @mock.patch('time.sleep', side_effect=ExitTestNormally)
        @mock.patch('gevent.spawn')
        def test_unregister(self, spawn, sleep, select, dnsserviceregister, dnsserviceprocessresult):
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

            self.assertTrue(UUT.unregister(mock.sentinel.name, mock.sentinel.regtype))

            try:
                run()
            except ExitTestNormally:
                pass
            except:
                self.fail(msg="Run raised unexpected error: %s" % (traceback.print_exc(),))

            dnsserviceregister.return_value.close.assert_called_once_with()

        @mock.patch('pybonjour.DNSServiceProcessResult')
        @mock.patch('pybonjour.DNSServiceRegister')
        @mock.patch('select.select')
        @mock.patch('time.sleep', side_effect=ExitTestNormally)
        @mock.patch('gevent.spawn')
        def test_unregister_does_nothint_when_nothing_to_unregister(self, spawn, sleep, select, dnsserviceregister, dnsserviceprocessresult):
            txtRecord={ 'name' : "Test Text Record",
                        'foo' : 'bar' }
            callback = mock.MagicMock(name="callback")

            select.side_effect = [ [ [ dnsserviceregister.return_value, ], [], [] ],
                                   ExitTestNormally ]

            UUT = MDNSEngine()

            UUT.start()
            run = spawn.call_args[0][0]

            self.assertFalse(UUT.unregister(mock.sentinel.name, mock.sentinel.regtype))

            try:
                run()
            except ExitTestNormally:
                pass
            except:
                self.fail(msg="Run raised unexpected error: %s" % (traceback.print_exc(),))

            dnsserviceregister.return_value.close.assert_not_called()

        @mock.patch('pybonjour.DNSServiceProcessResult')
        @mock.patch('pybonjour.DNSServiceRegister')
        @mock.patch('select.select')
        @mock.patch('time.sleep', side_effect=ExitTestNormally)
        @mock.patch('gevent.spawn')
        def test_close(self, spawn, sleep, select, dnsserviceregister, dnsserviceprocessresult):
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

            UUT.close()

            dnsserviceregister.return_value.close.assert_called_once_with()

        @mock.patch('pybonjour.DNSServiceQueryRecord')
        @mock.patch('pybonjour.DNSServiceResolve')
        @mock.patch('pybonjour.DNSServiceBrowse')
        @mock.patch('pybonjour.DNSServiceProcessResult')
        @mock.patch('pybonjour.DNSServiceEnumerateDomains')
        def assert_callback_on_service_is_correct(self, UUT, run, regtype, DNSServiceEnumerateDomains, DNSServiceProcessResult, DNSServiceBrowse, DNSServiceResolve, DNSServiceQueryRecord, registerOnly=True, domain=None):
            callback = mock.MagicMock(name="callback")
            UUT.callback_on_services(regtype, callback, registerOnly=registerOnly, domain=domain)
            if domain is None:
                DNSServiceBrowse.assert_called_once_with(regtype=regtype, callBack=mock.ANY)
                browse_callback = DNSServiceBrowse.call_args[1]["callBack"]
                DNSServiceEnumerateDomains.assert_called_once_with(pybonjour.kDNSServiceFlagsBrowseDomains, callBack=mock.ANY)
                domain_callback = DNSServiceEnumerateDomains.call_args[1]["callBack"]
            else:
                DNSServiceBrowse.assert_called_once_with(regtype=regtype, callBack=mock.ANY, domain=domain)
                browse_callback = DNSServiceBrowse.call_args[1]["callBack"]
                domain_callback = None

            with mock.patch('select.select', side_effect=[ [ [DNSServiceBrowse.return_value,], [], [] ], ExitTestNormally ]) as select:
                with self.assertRaises(ExitTestNormally):
                    run()
                self.assertIn(DNSServiceBrowse.return_value, select.call_args[0][0])
            DNSServiceProcessResult.assert_called_once_with(DNSServiceBrowse.return_value)
            # In real code this would then trigger the assigned callback, so let's test its behaviour

            # First check an error code results in a bugout
            callback.reset_mock()
            browse_callback(mock.sentinel.sdRef,
                                mock.sentinel.flags,
                                mock.sentinel.interfaceIndex,
                                mock.sentinel.errorCode,
                                mock.sentinel.serviceName,
                                regtype,
                                mock.sentinel.replyDomain)
            callback.assert_not_called()

            # Next check that a remove is handled as a bugout or a remove
            callback.reset_mock()
            browse_callback(mock.sentinel.sdRef,
                                0,
                                mock.sentinel.interfaceIndex,
                                pybonjour.kDNSServiceErr_NoError,
                                mock.sentinel.serviceName,
                                regtype,
                                mock.sentinel.replyDomain)
            if not registerOnly:
                callback.assert_called_once_with({"action": "remove", "name": mock.sentinel.serviceName, "type": regtype})
            else:
                callback.assert_not_called()

            # Next check that an add on .local is handled
            callback.reset_mock()
            browse_callback(mock.sentinel.sdRef,
                                pybonjour.kDNSServiceFlagsAdd,
                                mock.sentinel.interfaceIndex,
                                pybonjour.kDNSServiceErr_NoError,
                                mock.sentinel.serviceName,
                                regtype,
                                "local.")
            DNSServiceResolve.assert_called_once_with(0,
                                                      mock.sentinel.interfaceIndex,
                                                      mock.sentinel.serviceName,
                                                      regtype,
                                                      "local.",
                                                      mock.ANY)
            resolve_callback = DNSServiceResolve.call_args[0][5]
            with mock.patch('select.select', side_effect=[ [ [DNSServiceResolve.return_value,], [], [] ], ExitTestNormally ]) as select:
                with self.assertRaises(ExitTestNormally):
                    run()
                self.assertIn(DNSServiceResolve.return_value, select.call_args[0][0])
            DNSServiceProcessResult.assert_called_with(DNSServiceResolve.return_value)

            # Next check that an add on .example is handled
            callback.reset_mock()
            browse_callback(mock.sentinel.sdRef,
                                pybonjour.kDNSServiceFlagsAdd,
                                mock.sentinel.interfaceIndex,
                                pybonjour.kDNSServiceErr_NoError,
                                "service_name",
                                regtype,
                                "example")
            DNSServiceQueryRecord.assert_called_once_with(interfaceIndex=mock.sentinel.interfaceIndex,
                                                              fullname='service_name.example',
                                                              rrtype = pybonjour.kDNSServiceType_SRV,
                                                              callBack = mock.ANY)
            query_SRV_callback = DNSServiceQueryRecord.call_args[1]["callBack"]
            with mock.patch('select.select', side_effect=[ [ [DNSServiceQueryRecord.return_value,], [], [] ], ExitTestNormally ]) as select:
                with self.assertRaises(ExitTestNormally):
                    run()
                self.assertIn(DNSServiceQueryRecord.return_value, select.call_args[0][0])
            DNSServiceProcessResult.assert_called_with(DNSServiceQueryRecord.return_value)

            #Now check the query_SRV_callback behaves correctly
            query_SRV_callback(DNSServiceQueryRecord.return_value,
                                   mock.sentinel.flags,
                                   mock.sentinel.interfaceIndex,
                                   pybonjour.kDNSServiceErr_NoError,
                                   mock.sentinel.fullname,
                                   mock.sentinel.rrtype,
                                   mock.sentinel.rrclass,
                                   mock.sentinel.rdata,
                                   mock.sentinel.ttl)
            DNSServiceQueryRecord.return_value.close.assert_called_once_with()


            # Now to the given callback for resolve

            # Check an error results in a bugout
            callback.reset_mock()
            resolve_callback(mock.sentinel.sdRef,
                            mock.sentinel.flags,
                            mock.sentinel.interfaceIndex,
                            mock.sentinel.errorCode,
                            mock.sentinel.fullname,
                            mock.sentinel.hosttarget,
                            mock.sentinel.port,
                            mock.sentinel.txtRecord)
            callback.assert_not_called()

            # Check a non error calls through to a query
            DNSServiceQueryRecord.reset_mock()
            callback.reset_mock()
            DNSServiceQueryRecord.return_value = mock.MagicMock(name="DNSServiceQueryRecord()")
            resolve_callback(DNSServiceResolve.return_value,
                            mock.sentinel.flags,
                            mock.sentinel.interfaceIndex,
                            pybonjour.kDNSServiceErr_NoError,
                            mock.sentinel.fullname,
                            mock.sentinel.hosttarget,
                            mock.sentinel.port,
                            pybonjour.TXTRecord())
            callback.assert_not_called()
            DNSServiceQueryRecord.assert_called_once_with(interfaceIndex=mock.sentinel.interfaceIndex,
                                                        fullname=mock.sentinel.hosttarget,
                                                        rrtype=pybonjour.kDNSServiceType_A,
                                                        callBack=mock.ANY)
            query_record_callback = DNSServiceQueryRecord.call_args[1]["callBack"]
            with mock.patch('select.select', side_effect=[ [ [DNSServiceQueryRecord.return_value,], [], [] ], ExitTestNormally ]) as select:
                with self.assertRaises(ExitTestNormally):
                    run()
                self.assertIn(DNSServiceQueryRecord.return_value, select.call_args[0][0])
            DNSServiceProcessResult.assert_called_with(DNSServiceQueryRecord.return_value)
            DNSServiceResolve.return_value.close.assert_called_once_with()

            # Next check query_record_callback
            callback.reset_mock()
            with mock.patch('socket.inet_ntoa') as inet_ntoa:
                query_record_callback(DNSServiceQueryRecord.return_value,
                                    mock.sentinel.flags,
                                    mock.sentinel.interfaceIndex,
                                    pybonjour.kDNSServiceErr_NoError,
                                    mock.sentinel.fullname,
                                    mock.sentinel.rrtype,
                                    mock.sentinel.rrclass,
                                    mock.sentinel.rdata,
                                    mock.sentinel.ttl)
                inet_ntoa.assert_called_once_with(mock.sentinel.rdata)
                callback.assert_called_once_with({"action": "add", "name": mock.sentinel.serviceName, "type": regtype, "address": inet_ntoa.return_value, "port": mock.sentinel.port, "txt": dict(pybonjour.TXTRecord()), "interface": mock.sentinel.interfaceIndex})
            DNSServiceQueryRecord.return_value.close.assert_called_once_with()

            if domain_callback is not None:
                DNSServiceBrowse.reset_mock()
                domain_callback(DNSServiceEnumerateDomains.return_value,
                                mock.sentinel.flags,
                                mock.sentinel.interfaceIndex,
                                pybonjour.kDNSServiceErr_NoError,
                                mock.sentinel.new_domain)
                DNSServiceBrowse.assert_called_once_with(regtype=regtype,
                                                        callBack=mock.ANY,
                                                        domain=mock.sentinel.new_domain)

                DNSServiceBrowse.reset_mock()
                domain_callback(DNSServiceEnumerateDomains.return_value,
                                mock.sentinel.flags,
                                mock.sentinel.interfaceIndex,
                                pybonjour.kDNSServiceErr_Invalid,
                                mock.sentinel.new_domain)
                DNSServiceBrowse.assert_not_called()


        @mock.patch('gevent.spawn')
        def test_callback_on_services(self, spawn):
            UUT = MDNSEngine()

            UUT.start()
            run = spawn.call_args[0][0]

            self.assert_callback_on_service_is_correct(UUT, run, mock.sentinel.regtype, registerOnly=True, domain=None)

        @mock.patch('gevent.spawn')
        def test_callback_on_services_with_domain(self, spawn):
            UUT = MDNSEngine()

            UUT.start()
            run = spawn.call_args[0][0]

            self.assert_callback_on_service_is_correct(UUT, run, mock.sentinel.regtype, registerOnly=True, domain="potato.com")

        @mock.patch('gevent.spawn')
        def test_callback_on_services_without_register_only(self, spawn):
            UUT = MDNSEngine()

            UUT.start()
            run = spawn.call_args[0][0]

            self.assert_callback_on_service_is_correct(UUT, run, mock.sentinel.regtype, registerOnly=False, domain=None)

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

try:
    import avahi
except:
    pass
else:
    class TestMDNSEngine(unittest.TestCase):
        def setUp(self):
            paths = [ "nmoscommon.mdns.avahidbus.monkey",
                    "nmoscommon.mdns.avahidbus.DBusGMainLoop",
                    "dbus.SystemBus",
                    "dbus.Interface",
                    "gobject.MainLoop",
                    "glib.idle_add" ]
            patchers = { name : mock.patch(name) for name in paths }
            self.mocks = { name : patcher.start() for (name, patcher) in patchers.iteritems() }
            for (name, patcher) in patchers.iteritems():
                self.addCleanup(patcher.stop)

            self.mocks["gobject.MainLoop"].return_value.is_running.return_value = False
            def set_rval(tgt, val):
                def __inner():
                    tgt.return_value = val
                return __inner
            self.mocks["gobject.MainLoop"].return_value.run.side_effect = set_rval(self.mocks["gobject.MainLoop"].return_value.is_running, True)
            self.objects = mock.MagicMock(name="DBUSOBJECT")
            self.mocks["dbus.SystemBus"].return_value.get_object.side_effect = lambda _,path : self.DBUSObject(path)
            self.mocks["dbus.Interface"].side_effect = self.DBUSInterface

            def printmsg(t):
                def _inner(msg):
                    print t + ": " + msg
                return _inner

#        self.mocks['nmoscommon.facade.Logger'].return_value.writeInfo.side_effect = printmsg("INFO")
#        self.mocks['nmoscommon.facade.Logger'].return_value.writeWarning.side_effect = printmsg("WARNING")
#        self.mocks['nmoscommon.facade.Logger'].return_value.writeDebug.side_effect = printmsg("DEBUG")
#        self.mocks['nmoscommon.facade.Logger'].return_value.writeError.side_effect = printmsg("ERROR")
#        self.mocks['nmoscommon.facade.Logger'].return_value.writeFatal.side_effect = printmsg("FATAL")

        def DBUSObject(self, path):
            return getattr(self.objects, path)

        def DBUSInterface(self, obj, interface):
            return getattr(obj, interface)

        def test_init(self):
            from nmoscommon.mdns.avahidbus import MDNSEngine
            UUT = MDNSEngine()

            self.mocks["nmoscommon.mdns.avahidbus.DBusGMainLoop"].assert_called_once_with()
            self.mocks["dbus.SystemBus"].assert_called_once_with(mainloop=self.mocks["nmoscommon.mdns.avahidbus.DBusGMainLoop"].return_value)
            self.mocks["dbus.SystemBus"].return_value.get_object.assert_called_once_with(avahi.DBUS_NAME, '/')
            self.mocks["dbus.Interface"].assert_called_once_with(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server')

        def test_start_starts_a_glib_mainloop_with_gevent_idling(self):
            """For glib and gevent to play nicely we must insert an idle handler in glib which calls gevent.sleep"""
            from nmoscommon.mdns.avahidbus import MDNSEngine
            UUT = MDNSEngine()

            def run_and_return_mock(f):
                f()
                return mock.DEFAULT

            with mock.patch('gevent.spawn', side_effect=run_and_return_mock) as spawn:
                UUT.start()
            self.mocks['glib.idle_add'].assert_called_once_with(mock.ANY)
            self.mocks['gobject.MainLoop'].return_value.run.assert_called_once_with()
            idler = self.mocks['glib.idle_add'].call_args[0][0]

            with mock.patch('gevent.sleep') as sleep:
                self.assertTrue(idler())
                sleep.assert_called_with(mock.ANY)
                
            UUT.stop()
            self.mocks['gobject.MainLoop'].return_value.quit.assert_called_once_with()

        def assert_register_is_correct(self, name, regtype, port, txtRecord, current_state=avahi.ENTRY_GROUP_UNCOMMITED):
            from nmoscommon.mdns.avahidbus import MDNSEngine
            UUT = MDNSEngine()

            callback=mock.MagicMock(name='callback')

            #EntryGroupNew should return the path of a new Entry Group object
            self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').EntryGroupNew.side_effect = [ "/new_entry_group_object", Exception ]
            entrygroup = self.DBUSInterface(self.DBUSObject("/new_entry_group_object"), avahi.DBUS_INTERFACE_ENTRY_GROUP)
            entrygroup.GetState.return_value = current_state

            UUT.register(name, regtype, port, txtRecord=txtRecord, callback=callback)

            if txtRecord is None:
                txtRecord = {}

            if current_state != avahi.ENTRY_GROUP_ESTABLISHED:
                entrygroup.Reset.assert_not_called()
            else:
                entrygroup.Reset.assert_called_once_with()
            entrygroup.connect_to_signal.assert_called_once_with("StateChanged", mock.ANY)
            entrygroup.AddService.assert_called_once_with(avahi.IF_UNSPEC,
                                                          avahi.PROTO_UNSPEC,
                                                          dbus.UInt32(0),
                                                          name,
                                                          regtype,
                                                          "local",
                                                          '',
                                                          port,
                                                          avahi.dict_to_txt_array(txtRecord))
            entrygroup.Commit.assert_called_once_with()

            # Should have subscribed to the StateChanged signal, make sure it calls through to the right callback
            entrygroup.connect_to_signal.call_args[0][1](avahi.ENTRY_GROUP_COLLISION, "SHOULD BE IGNORED")
            callback.assert_called_once_with({ "action" : "collision", "name" : name, "regtype" : regtype, "port" : port, "txtRecord" : txtRecord})
            callback.reset_mock()

            entrygroup.connect_to_signal.call_args[0][1](avahi.ENTRY_GROUP_ESTABLISHED, "SHOULD BE IGNORED")
            callback.assert_called_once_with({ "action" : "established", "name" : name, "regtype" : regtype, "port" : port, "txtRecord" : txtRecord})
            callback.reset_mock()

            entrygroup.connect_to_signal.call_args[0][1](avahi.ENTRY_GROUP_FAILURE, "SHOULD BE IGNORED")
            callback.assert_called_once_with({ "action" : "failure", "name" : name, "regtype" : regtype, "port" : port, "txtRecord" : txtRecord})
            callback.reset_mock()

            return (UUT, entrygroup)

        def test_register_new_service(self):
            name = "test_name"
            regtype = "test_type"
            port = 12345
            txtRecord={ 'name' : "Test Text Record",
                        'foo' : 'bar' }
            self.assert_register_is_correct(name, regtype, port, txtRecord, current_state=avahi.ENTRY_GROUP_UNCOMMITED)

        def test_register_new_service_without_txt_record(self):
            name = "test_name"
            regtype = "test_type"
            port = 12345
            self.assert_register_is_correct(name, regtype, port, None, current_state=avahi.ENTRY_GROUP_UNCOMMITED)

        def test_reregister_service(self):
            name = "test_name"
            regtype = "test_type"
            port = 12345
            txtRecord={ 'name' : "Test Text Record",
                        'foo' : 'bar' }
            self.assert_register_is_correct(name, regtype, port, txtRecord, current_state=avahi.ENTRY_GROUP_ESTABLISHED)

        def test_update(self):
            name = "test_name"
            regtype = "test_type"
            port = 12345
            oldtxtRecord={ 'name' : "Test Text Record",
                           'foo' : 'bar' }
            newtxtRecord={ 'name' : "Test Text Record",
                           'foo' : 'baz' }
            (UUT, entrygroup) = self.assert_register_is_correct(name, regtype, port, oldtxtRecord, current_state=avahi.ENTRY_GROUP_ESTABLISHED)
            UUT.update(name, regtype, txtRecord=newtxtRecord)
            entrygroup.UpdateServiceTxt.assert_called_once_with(avahi.IF_UNSPEC,
                                                                avahi.PROTO_UNSPEC,
                                                                dbus.UInt32(0),
                                                                name,
                                                                regtype,
                                                                "local.",
                                                                avahi.dict_to_txt_array(newtxtRecord))

        def test_update_to_remove_txt_record(self):
            name = "test_name"
            regtype = "test_type"
            port = 12345
            oldtxtRecord={ 'name' : "Test Text Record",
                           'foo' : 'bar' }
            (UUT, entrygroup) = self.assert_register_is_correct(name, regtype, port, oldtxtRecord, current_state=avahi.ENTRY_GROUP_ESTABLISHED)
            UUT.update(name, regtype)
            entrygroup.UpdateServiceTxt.assert_called_once_with(avahi.IF_UNSPEC,
                                                                avahi.PROTO_UNSPEC,
                                                                dbus.UInt32(0),
                                                                name,
                                                                regtype,
                                                                "local.",
                                                                avahi.dict_to_txt_array({}))

        def test_unregister(self):
            name = "test_name"
            regtype = "test_type"
            port = 12345
            oldtxtRecord={ 'name' : "Test Text Record",
                           'foo' : 'bar' }
            (UUT, entrygroup) = self.assert_register_is_correct(name, regtype, port, oldtxtRecord, current_state=avahi.ENTRY_GROUP_ESTABLISHED)
            UUT.unregister(name, regtype)
            entrygroup.Free.assert_called_once_with()

        def test_unregister_is_idempotent(self):
            name = "test_name"
            regtype = "test_type"
            port = 12345
            oldtxtRecord={ 'name' : "Test Text Record",
                           'foo' : 'bar' }
            (UUT, entrygroup) = self.assert_register_is_correct(name, regtype, port, oldtxtRecord, current_state=avahi.ENTRY_GROUP_ESTABLISHED)
            UUT.unregister(name, regtype)
            UUT.unregister(name, regtype)
            entrygroup.Free.assert_called_once_with()

        def test_unregister_does_nothing_when_nothing_to_be_done(self):
            from nmoscommon.mdns.avahidbus import MDNSEngine
            UUT = MDNSEngine()

            name = "test_name"
            regtype = "test_type"

            entrygroup = self.DBUSInterface(self.DBUSObject("/new_entry_group_object"), avahi.DBUS_INTERFACE_ENTRY_GROUP)

            UUT.unregister(name, regtype)
            entrygroup.Free.assert_not_called()

        def test_callback_on_services_with_domain(self):
            self.assert_callback_on_services_calls_back(domain="potato")

        def test_callback_on_services_without_domain(self):
            self.assert_callback_on_services_calls_back()

        def assert_callback_on_services_calls_back(self, domain=None):
            from nmoscommon.mdns.avahidbus import MDNSEngine
            UUT = MDNSEngine()

            callback = mock.MagicMock(name="callback")
            regtype = "test_type"
            txtrecord={ 'name' : "Test Text Record",
                        'foo' : 'bar' }

            if domain is None:
                expected_domain = "local"
                detected_domain = "dummydomain"
            else:
                expected_domain = domain

            self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').DomainBrowserNew.side_effect = [ "/new_domain_browser", Exception ]
            self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').ServiceBrowserNew.side_effect = lambda i,p,t,domain,n : "/new_service_browser(" + domain + ")"
            dbrowser = self.DBUSInterface(self.DBUSObject("/new_domain_browser"), avahi.DBUS_INTERFACE_DOMAIN_BROWSER)
            sbrowser = self.DBUSInterface(self.DBUSObject("/new_service_browser(" + expected_domain + ")"), avahi.DBUS_INTERFACE_SERVICE_BROWSER)
            if domain is None:
                dsbrowser = self.DBUSInterface(self.DBUSObject("/new_service_browser(" + detected_domain + ")"), avahi.DBUS_INTERFACE_SERVICE_BROWSER)

            UUT.callback_on_services(regtype, callback, registerOnly=True, domain=domain)

            if domain is None:
                self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').DomainBrowserNew.assert_called_with(avahi.IF_UNSPEC,
                                                                                                                             avahi.PROTO_UNSPEC,
                                                                                                                             "",
                                                                                                                             0,
                                                                                                                             dbus.UInt32(0))
                dbrowser.connect_to_signal.assert_called_with("ItemNew", mock.ANY)

            self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').ServiceBrowserNew.assert_called_with(avahi.IF_UNSPEC,
                                                                                                                          avahi.PROTO_UNSPEC,
                                                                                                                          regtype,
                                                                                                                          expected_domain,
                                                                                                                          dbus.UInt32(0))
            service_callbacks = dict((call[1][0], call[1][1]) for call in sbrowser.connect_to_signal.mock_calls)
            self.assertIn("ItemNew", service_callbacks)
            self.assertIn("ItemRemove", service_callbacks)

            # Now test the ItemNew Callback calls ResolveService
            service_callbacks["ItemNew"](mock.sentinel.interface, mock.sentinel.protocol, mock.sentinel.name, mock.sentinel.stype, mock.sentinel.domain, mock.sentinel.flags)
            self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').ResolveService.assert_called_with(mock.sentinel.interface,
                                                                                                                       mock.sentinel.protocol,
                                                                                                                       mock.sentinel.name,
                                                                                                                       mock.sentinel.stype,
                                                                                                                       mock.sentinel.domain,
                                                                                                                       avahi.PROTO_UNSPEC,
                                                                                                                       dbus.UInt32(0),
                                                                                                                       reply_handler=mock.ANY,
                                                                                                                       error_handler=mock.ANY)
            # Now check that the reply_handler passed to ResolveService will call back correctly
            callback.reset_mock()
            resolve_service_reply_handler = self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').ResolveService.call_args[1]['reply_handler']
            resolve_service_reply_handler(mock.sentinel.interface,
                                          mock.sentinel.protocol,
                                          mock.sentinel.name,
                                          mock.sentinel.stype,
                                          mock.sentinel.domain,
                                          mock.sentinel.host,
                                          mock.sentinel.arprotocol,
                                          mock.sentinel.address,
                                          mock.sentinel.port,
                                          avahi.dict_to_txt_array(txtrecord),
                                          mock.sentinel.flags)
            callback.assert_called_once_with({"action": "add",
                                              "name": mock.sentinel.name,
                                              "type": mock.sentinel.stype,
                                              "address": mock.sentinel.address,
                                              "port": mock.sentinel.port,
                                              "txt": txtrecord,
                                              "interface": mock.sentinel.interface})

            # Test error_handler is callable
            resolve_service_error_handler = self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').ResolveService.call_args[1]['error_handler']
            try:
                resolve_service_error_handler("Not Really An Error, just testing Error Reporting")
            except:
                self.fail(msg="error_handler passed to ResolveService threw unknown exception: %s" % (traceback.format_exc(),))

            # Now test the ItemRemove Callback calls back correctly
            callback.reset_mock()
            service_callbacks["ItemRemove"](mock.sentinel.interface, mock.sentinel.protocol, mock.sentinel.name, mock.sentinel._type, mock.sentinel.domain, mock.sentinel.flags)
            callback.assert_called_once_with({"action": "remove", "name": mock.sentinel.name, "type": mock.sentinel._type})

            if domain is None:
                # Check that the domain browser callback sets up a new service browser for the new domain
                self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').ServiceBrowserNew.reset_mock()
                callback.reset_mock()
                domain_callbacks = dict((call[1][0], call[1][1]) for call in dbrowser.connect_to_signal.mock_calls)

                domain_callbacks['ItemNew'](mock.sentinel.interface, mock.sentinel.protocol, detected_domain, mock.sentinel.flags)
                self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').ServiceBrowserNew.assert_called_with(avahi.IF_UNSPEC,
                                                                                                                              avahi.PROTO_UNSPEC,
                                                                                                                              regtype,
                                                                                                                              detected_domain,
                                                                                                                              dbus.UInt32(0))
                service_callbacks = dict((call[1][0], call[1][1]) for call in dsbrowser.connect_to_signal.mock_calls)
                self.assertIn("ItemNew", service_callbacks)
                self.assertIn("ItemRemove", service_callbacks)

                # Now test the ItemNew Callback calls ResolveService
                service_callbacks["ItemNew"](mock.sentinel.interface, mock.sentinel.protocol, mock.sentinel.name, mock.sentinel.stype, mock.sentinel.domain, mock.sentinel.flags)
                self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').ResolveService.assert_called_with(mock.sentinel.interface,
                                                                                                                       mock.sentinel.protocol,
                                                                                                                       mock.sentinel.name,
                                                                                                                       mock.sentinel.stype,
                                                                                                                       mock.sentinel.domain,
                                                                                                                       avahi.PROTO_UNSPEC,
                                                                                                                       dbus.UInt32(0),
                                                                                                                       reply_handler=mock.ANY,
                                                                                                                       error_handler=mock.ANY)
                # Now check that the reply_handler passed to ResolveService will call back correctly
                callback.reset_mock()
                resolve_service_reply_handler = self.DBUSInterface(self.DBUSObject('/'), 'org.freedesktop.Avahi.Server').ResolveService.call_args[1]['reply_handler']
                resolve_service_reply_handler(mock.sentinel.interface,
                                          mock.sentinel.protocol,
                                          mock.sentinel.name,
                                          mock.sentinel.stype,
                                          mock.sentinel.domain,
                                          mock.sentinel.host,
                                          mock.sentinel.arprotocol,
                                          mock.sentinel.address,
                                          mock.sentinel.port,
                                          avahi.dict_to_txt_array(txtrecord),
                                          mock.sentinel.flags)
                callback.assert_called_once_with({"action": "add",
                                              "name": mock.sentinel.name,
                                              "type": mock.sentinel.stype,
                                              "address": mock.sentinel.address,
                                              "port": mock.sentinel.port,
                                              "txt": txtrecord,
                                              "interface": mock.sentinel.interface})

        def test_close(self):
            name = "test_name"
            regtype = "test_type"
            port = 12345
            oldtxtRecord={ 'name' : "Test Text Record",
                           'foo' : 'bar' }
            (UUT, entrygroup) = self.assert_register_is_correct(name, regtype, port, oldtxtRecord, current_state=avahi.ENTRY_GROUP_ESTABLISHED)
            UUT.close()
            entrygroup.Free.assert_called_once_with()

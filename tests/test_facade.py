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
from nmoscommon.facade import *

class TestFacade(unittest.TestCase):
    def setUp(self):
        paths = ['nmoscommon.facade.Logger',
                 'nmoscommon.facade.Proxy', ]
        patchers = { name : mock.patch(name) for name in paths }
        self.mocks = { name : patcher.start() for (name, patcher) in patchers.iteritems() }
        for (name, patcher) in patchers.iteritems():
            self.addCleanup(patcher.stop)
        def _invoke_named(obj):
            def __inner(method, *args, **kwargs):
                return getattr(obj, method)(*args, **kwargs)
            return __inner
        self.mocks['nmoscommon.facade.Proxy'].return_value.invoke_named.side_effect = _invoke_named(self.mocks['nmoscommon.facade.Proxy'].return_value)

        def printmsg(t):
            def _inner(msg):
                print t + ": " + msg
            return _inner

#        self.mocks['nmoscommon.facade.Logger'].return_value.writeInfo.side_effect = printmsg("INFO")
#        self.mocks['nmoscommon.facade.Logger'].return_value.writeWarning.side_effect = printmsg("WARNING")
#        self.mocks['nmoscommon.facade.Logger'].return_value.writeDebug.side_effect = printmsg("DEBUG")
#        self.mocks['nmoscommon.facade.Logger'].return_value.writeError.side_effect = printmsg("ERROR")
#        self.mocks['nmoscommon.facade.Logger'].return_value.writeFatal.side_effect = printmsg("FATAL")

    def test_setup_ipc(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        UUT = Facade("dummy_type", address=address)
        UUT.setup_ipc()

        self.mocks['nmoscommon.facade.Proxy'].assert_called_once_with(address)
        self.assertEqual(self.mocks['nmoscommon.facade.Proxy'].return_value, UUT.ipc)

    def test_setup_ipc_exception_handling(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        UUT = Facade("dummy_type", address=address)

        self.mocks['nmoscommon.facade.Proxy'].side_effect = Exception

        UUT.setup_ipc()

        self.mocks['nmoscommon.facade.Proxy'].assert_called_once_with(address)
        self.assertIsNone(UUT.ipc)

    def test_register_service(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.return_value = FAC_SUCCESS

        href = "http://dummy.example.com"
        proxy_path = "http://dummyproxy.example.com"
        UUT.register_service(href, proxy_path)

        self.assertIsNotNone(UUT.ipc)
        UUT.ipc.srv_register.assert_called_once_with(srv_type, "urn:x-ipstudio:service:" + srv_type, mock.ANY, href, proxy_path)
        self.assertTrue(UUT.srv_registered)

    def test_register_service_bails_when_no_ipc(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].side_effect = Exception

        href = "http://dummy.example.com"
        proxy_path = "http://dummyproxy.example.com"
        UUT.register_service(href, proxy_path)

        self.assertIsNone(UUT.ipc)
        self.assertFalse(UUT.srv_registered)

    def test_register_service_bails_when_register_fails(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.return_value = FAC_OTHERERROR

        href = "http://dummy.example.com"
        proxy_path = "http://dummyproxy.example.com"
        UUT.register_service(href, proxy_path)

        self.assertIsNotNone(UUT.ipc)
        UUT.ipc.srv_register.assert_called_once_with(srv_type, "urn:x-ipstudio:service:" + srv_type, mock.ANY, href, proxy_path)
        self.assertFalse(UUT.srv_registered)

    def test_register_service_bails_when_register_raises(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.side_effect = Exception

        href = "http://dummy.example.com"
        proxy_path = "http://dummyproxy.example.com"
        UUT.register_service(href, proxy_path)

        self.assertIsNone(UUT.ipc)
        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.assert_called_once_with(srv_type, "urn:x-ipstudio:service:" + srv_type, mock.ANY, href, proxy_path)
        self.assertFalse(UUT.srv_registered)

    def test_unregister_service(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        UUT.srv_registered = True
        UUT.unregister_service()

        self.assertIsNotNone(UUT.ipc)
        UUT.ipc.srv_unregister.assert_called_once_with(srv_type, mock.ANY)
        self.assertFalse(UUT.srv_registered)

    def test_unregister_service_bails_when_no_ipc(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].side_effect = Exception

        UUT.srv_registered = True
        UUT.unregister_service()

        self.assertIsNone(UUT.ipc)
        self.assertTrue(UUT.srv_registered)

    def test_unregister_service_bails_when_unregister_raises(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_unregister.side_effect = Exception

        UUT.srv_registered = True
        UUT.unregister_service()

        self.assertIsNone(UUT.ipc)
        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_unregister.assert_called_once_with(srv_type, mock.ANY)
        self.assertTrue(UUT.srv_registered)

    def test_heartbeat_service(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_heartbeat.return_value = FAC_SUCCESS

        with mock.patch.object(UUT, 'reregister_all') as reregister_all:
            UUT.heartbeat_service()

            self.assertTrue(UUT.srv_registered)
            self.mocks['nmoscommon.facade.Proxy'].return_value.srv_heartbeat.assert_called_once_with(srv_type, mock.ANY)
            reregister_all.assert_not_called()

    def test_heartbeat_service_bails_when_no_ipc(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].side_effect = Exception

        with mock.patch.object(UUT, 'reregister_all') as reregister_all:
            UUT.heartbeat_service()

            self.assertFalse(UUT.srv_registered)
            self.mocks['nmoscommon.facade.Proxy'].return_value.srv_heartbeat.assert_not_called()
            reregister_all.assert_not_called()

    def test_heartbeat_service_bails_when_heartbeat_raises(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_heartbeat.side_effect = Exception

        with mock.patch.object(UUT, 'reregister_all') as reregister_all:
            UUT.heartbeat_service()

            self.assertFalse(UUT.srv_registered)
            self.mocks['nmoscommon.facade.Proxy'].return_value.srv_heartbeat.assert_called_once_with(srv_type, mock.ANY)
            reregister_all.assert_not_called()

    def test_heartbeat_service_reregisters_on_failure(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_heartbeat.return_value = FAC_OTHERERROR

        with mock.patch.object(UUT, 'reregister_all') as reregister_all:
            UUT.heartbeat_service()

            self.assertFalse(UUT.srv_registered)
            self.mocks['nmoscommon.facade.Proxy'].return_value.srv_heartbeat.assert_called_once_with(srv_type, mock.ANY)
            reregister_all.assert_called_once_with()

    def test_heartbeat_service_reregisters_on_success_when_told_to(self):
        """Is this correct? This is current behaviour, but doesn't match the comments"""
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_heartbeat.return_value = FAC_SUCCESS

        with mock.patch.object(UUT, 'reregister_all') as reregister_all:
            UUT.reregister = True
            UUT.heartbeat_service()

            self.assertTrue(UUT.srv_registered)
            self.mocks['nmoscommon.facade.Proxy'].return_value.srv_heartbeat.assert_called_once_with(srv_type, mock.ANY)
            reregister_all.assert_called_once_with()

    def assert_method_calls_remote_method_or_bails(self, method_name, remote_method_name, params, registered=True, ipc=True, raises=False, presetup=None, extra_check=None):
        getattr(self.mocks['nmoscommon.facade.Proxy'].return_value, remote_method_name).reset_mock()
        getattr(self.mocks['nmoscommon.facade.Proxy'].return_value, remote_method_name).side_effect = None
        self.mocks['nmoscommon.facade.Proxy'].side_effect = None

        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        if presetup is not None:
            presetup(UUT)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.return_value = FAC_SUCCESS

        if registered:
            href = "http://dummy.example.com"
            proxy_path = "http://dummyproxy.example.com"
            UUT.register_service(href, proxy_path)

        if not ipc:
            UUT.ipc = None
            self.mocks['nmoscommon.facade.Proxy'].side_effect = Exception

        if raises:
            getattr(self.mocks['nmoscommon.facade.Proxy'].return_value, remote_method_name).side_effect = Exception

        getattr(UUT, method_name)(*params)
        if registered and ipc:
            callparams = [srv_type, mock.ANY] + list(params)
            getattr(self.mocks['nmoscommon.facade.Proxy'].return_value, remote_method_name).assert_called_once_with(*callparams)
        elif not registered or not ipc:
            getattr(self.mocks['nmoscommon.facade.Proxy'].return_value, remote_method_name).assert_not_called()
            self.assertTrue(UUT.reregister)
        if raises:
            self.assertTrue(UUT.reregister)
        if extra_check is not None:
            extra_check(UUT)

    def test_addResource(self):
        def _extra_check(UUT):
            self.assertIn("dummykey", UUT.resources["dummytype"])
            self.assertEqual(UUT.resources["dummytype"]["dummykey"], "dummyval")
        self.assert_method_calls_remote_method_or_bails('addResource', 'res_register', ("dummytype", "dummykey", "dummyval"), extra_check=_extra_check)
        self.assert_method_calls_remote_method_or_bails('addResource', 'res_register', ("dummytype", "dummykey", "dummyval"), registered=False)
        self.assert_method_calls_remote_method_or_bails('addResource', 'res_register', ("dummytype", "dummykey", "dummyval"), ipc=False)
        self.assert_method_calls_remote_method_or_bails('addResource', 'res_register', ("dummytype", "dummykey", "dummyval"), raises=True)

    def test_updateResource(self):
        def _extra_check(UUT):
            self.assertIn("dummykey", UUT.resources["dummytype"])
            self.assertEqual(UUT.resources["dummytype"]["dummykey"], "dummyval")            
        self.assert_method_calls_remote_method_or_bails('updateResource', 'res_update', ("dummytype", "dummykey", "dummyval"), extra_check=_extra_check)
        self.assert_method_calls_remote_method_or_bails('updateResource', 'res_update', ("dummytype", "dummykey", "dummyval"), registered=False)
        self.assert_method_calls_remote_method_or_bails('updateResource', 'res_update', ("dummytype", "dummykey", "dummyval"), ipc=False)
        self.assert_method_calls_remote_method_or_bails('updateResource', 'res_update', ("dummytype", "dummykey", "dummyval"), raises=True)

    def test_delResource(self):
        def _presetup(UUT):
            if "flow" not in UUT.resources:
                UUT.resources["flow"] = {}
            if "transport" not in UUT.resources:
                UUT.resources["transport"] = {}
            UUT.resources["flow"]["dummykey"] = 'dummyval'
            UUT.resources["transport"]["dummytransportkey"] = { "flow-id" : "dummykey" }
        def _extra_check(UUT):
            self.assertNotIn("dummykey", UUT.resources["flow"])
            self.assertNotIn("dummytransportkey", UUT.resources["transport"])
        self.assert_method_calls_remote_method_or_bails('delResource', 'res_unregister', ("flow", "dummykey"), presetup=_presetup, extra_check=_extra_check)
        self.assert_method_calls_remote_method_or_bails('delResource', 'res_unregister', ("dummytype", "dummykey"), registered=False)
        self.assert_method_calls_remote_method_or_bails('delResource', 'res_unregister', ("dummytype", "dummykey"), ipc=False)
        self.assert_method_calls_remote_method_or_bails('delResource', 'res_unregister', ("dummytype", "dummykey"), raises=True)

    def test_addControl(self):
        def _extra_check(UUT):
            self.assertIn("dummyid", UUT.controls)
            self.assertIn("dummyhref", UUT.controls["dummyid"])
            self.assertEqual(UUT.controls["dummyid"]["dummyhref"], { "href" : "dummyhref" })
        self.assert_method_calls_remote_method_or_bails('addControl', 'control_register', ("dummyid", { "href" : "dummyhref" }), extra_check=_extra_check)
        self.assert_method_calls_remote_method_or_bails('addControl', 'control_register', ("dummyid", { "href" : "dummyhref" }), registered=False)
        self.assert_method_calls_remote_method_or_bails('addControl', 'control_register', ("dummyid", { "href" : "dummyhref" }), ipc=False)
        self.assert_method_calls_remote_method_or_bails('addControl', 'control_register', ("dummyid", { "href" : "dummyhref" }), raises=True)

    def test_delControl(self):
        def _presetup(UUT):
            if "dummyid" not in UUT.controls:
                UUT.controls["dummyid"] = {}
            UUT.controls["dummyid"]["dummyhref"] = 'dummyval'
        def _extra_check(UUT):
            self.assertNotIn("dummyhref", UUT.controls["dummyid"])
        self.assert_method_calls_remote_method_or_bails('delControl', 'control_unregister', ("dummyid", { "href" : "dummyhref" }), presetup=_presetup, extra_check=_extra_check)
        self.assert_method_calls_remote_method_or_bails('delControl', 'control_unregister', ("dummyid", { "href" : "dummyhref" }), registered=False)
        self.assert_method_calls_remote_method_or_bails('delControl', 'control_unregister', ("dummyid", { "href" : "dummyhref" }), ipc=False)
        self.assert_method_calls_remote_method_or_bails('delControl', 'control_unregister', ("dummyid", { "href" : "dummyhref" }), raises=True)

    def test_get_node_self(self):
        self.assert_method_calls_remote_method_or_bails('get_node_self', 'self_get', ("v1.1",))
        self.assert_method_calls_remote_method_or_bails('get_node_self', 'self_get', ("v1.1",), registered=False)
        self.assert_method_calls_remote_method_or_bails('get_node_self', 'self_get', ("v1.1",), ipc=False)
        self.assert_method_calls_remote_method_or_bails('get_node_self', 'self_get', ("v1.1",), raises=True)

    def test_debug_message(self):
        """There's not a lot we can sensibly check here, but we might as well check that every error has a message and that no two errors have the same message"""
        codes = [ name for name in dir() if name.startswith('FAC_') ]
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)
        
        msgs = [ UUT.debug_message(c) for c in codes ]

        for msg in msgs:
            self.assertEqual(msgs.count(msg), 1)

    def test_reregister_all(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.return_value = FAC_SUCCESS

        href = "http://dummy.example.com"
        proxy_path = "http://dummyproxy.example.com"
        UUT.register_service(href, proxy_path)

        resources = [ ("type0", "key0", "val0"),
                      ("type0", "key1", "val1"),
                      ("type2", "key2", "val2") ]
        controls = [ ("id0", { "href" : "href0" }),
                         ("id1", { "href" : "href1" }),
                         ("id2", { "href" : "href2" }),
                         ]

        for res in resources:
            UUT.addResource(*res)
        UUT.addResource("receiver", "rkey", {"pipel_id" : "DUMMY0", "pipeline_id" : "DUMMY1", "dummy" : "DUMMY2" } )

        for con in controls:
            UUT.addControl(*con)

        expected_res_register_calls = [ mock.call(srv_type, mock.ANY, *res) for res in resources ] + [ mock.call(srv_type, mock.ANY, "receiver", "rkey", { "dummy" : "DUMMY2" }), ]
        expected_control_register_calls = [ mock.call(srv_type, mock.ANY, *con) for con in controls ]

        UUT.ipc.res_register.reset_mock()
        UUT.ipc.control_register.reset_mock()

        UUT.reregister_all()

        self.assertFalse(UUT.reregister)
        self.assertTrue(UUT.srv_registered)
        self.assertItemsEqual(UUT.ipc.res_register.mock_calls, expected_res_register_calls)
        self.assertItemsEqual(UUT.ipc.control_register.mock_calls, expected_control_register_calls)

    def test_reregister_all_bails_if_failed_to_unregister(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.return_value = FAC_SUCCESS
        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_unregister.side_effect = Exception

        href = "http://dummy.example.com"
        proxy_path = "http://dummyproxy.example.com"
        UUT.register_service(href, proxy_path)

        UUT.ipc.res_register.reset_mock()
        UUT.ipc.control_register.reset_mock()

        UUT.reregister_all()

        self.mocks['nmoscommon.facade.Proxy'].return_value.res_register.assert_not_called()
        self.mocks['nmoscommon.facade.Proxy'].return_value.control_register.assert_not_called()

    def test_reregister_all_bails_if_failed_to_register(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.return_value = FAC_SUCCESS

        href = "http://dummy.example.com"
        proxy_path = "http://dummyproxy.example.com"
        UUT.register_service(href, proxy_path)

        UUT.ipc.res_register.reset_mock()
        UUT.ipc.control_register.reset_mock()

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.side_effect = Exception

        UUT.reregister_all()

        self.mocks['nmoscommon.facade.Proxy'].return_value.res_register.assert_not_called()
        self.mocks['nmoscommon.facade.Proxy'].return_value.control_register.assert_not_called()

    def test_reregister_all_bails_when_res_register_raises(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.return_value = FAC_SUCCESS

        href = "http://dummy.example.com"
        proxy_path = "http://dummyproxy.example.com"
        UUT.register_service(href, proxy_path)

        resources = [ ("type0", "key0", "val0"),
                      ("type0", "key1", "val1"),
                      ("type2", "key2", "val2") ]
        controls = [ ("id0", { "href" : "href0" }),
                         ("id1", { "href" : "href1" }),
                         ("id2", { "href" : "href2" }),
                         ]

        for res in resources:
            UUT.addResource(*res)
        UUT.addResource("receiver", "rkey", {"pipel_id" : "DUMMY0", "pipeline_id" : "DUMMY1", "dummy" : "DUMMY2" } )

        for con in controls:
            UUT.addControl(*con)

        UUT.ipc.res_register.reset_mock()
        UUT.ipc.control_register.reset_mock()

        UUT.ipc.res_register.side_effect = Exception

        with mock.patch('gevent.sleep') as sleep:
            UUT.reregister_all()

        self.assertIsNone(UUT.ipc)
        self.assertEqual(len(self.mocks['nmoscommon.facade.Proxy'].return_value.res_register.mock_calls), 1)
        self.assertEqual(len(self.mocks['nmoscommon.facade.Proxy'].return_value.control_register.mock_calls), 0)

    def test_reregister_all_bails_when_control_register_raises(self):
        address="ipc:///tmp/nmos-nodefacade.dummy.for.test"
        srv_type = "dummy_type"
        UUT = Facade(srv_type, address=address)

        self.mocks['nmoscommon.facade.Proxy'].return_value.srv_register.return_value = FAC_SUCCESS

        href = "http://dummy.example.com"
        proxy_path = "http://dummyproxy.example.com"
        UUT.register_service(href, proxy_path)

        resources = [ ("type0", "key0", "val0"),
                      ("type0", "key1", "val1"),
                      ("type2", "key2", "val2") ]
        controls = [ ("id0", { "href" : "href0" }),
                         ("id1", { "href" : "href1" }),
                         ("id2", { "href" : "href2" }),
                         ]

        for res in resources:
            UUT.addResource(*res)
        UUT.addResource("receiver", "rkey", {"pipel_id" : "DUMMY0", "pipeline_id" : "DUMMY1", "dummy" : "DUMMY2" } )

        expected_res_register_calls = [ mock.call(srv_type, mock.ANY, *res) for res in resources ] + [ mock.call(srv_type, mock.ANY, "receiver", "rkey", { "dummy" : "DUMMY2" }), ]

        for con in controls:
            UUT.addControl(*con)

        UUT.ipc.res_register.reset_mock()
        UUT.ipc.control_register.reset_mock()

        UUT.ipc.control_register.side_effect = Exception

        with mock.patch('gevent.sleep') as sleep:
            UUT.reregister_all()

        self.assertIsNone(UUT.ipc)
        self.assertItemsEqual(self.mocks['nmoscommon.facade.Proxy'].return_value.res_register.mock_calls, expected_res_register_calls)
        self.assertEqual(len(self.mocks['nmoscommon.facade.Proxy'].return_value.control_register.mock_calls), 1)

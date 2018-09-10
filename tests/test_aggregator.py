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

from six import iteritems, itervalues
from six import PY2

import unittest
import mock
from nmoscommon.aggregator import *
import nmoscommon.logger
from nmoscommon import nmoscommonconfig

class TestMDNSUpdater(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestMDNSUpdater, self).__init__(*args, **kwargs)
        if PY2:
            self.assertCountEqual = self.assertItemsEqual

    def test_init(self):
        """Test of initialisation of an MDNSUpdater"""
        mappings = {"device": "ver_dvc", "flow": "ver_flw", "source": "ver_src", "sender":"ver_snd", "receiver":"ver_rcv", "self":"ver_slf"}
        mdnstype = "_nmos-node._tcp"
        txt_recs = {"api_ver": "v1.0,v1.1,v1.2", "api_proto": "http"}
        mdnsname = "node_dummy_for_testing"
        port = 12345
        mdnsengine = mock.MagicMock()
        logger = mock.MagicMock()

        UUT = MDNSUpdater(mdnsengine, mdnstype, mdnsname, mappings, port, logger, txt_recs=txt_recs)
        self.assertEqual(UUT.mdns_type, mdnstype)
        self.assertEqual(UUT.mdns_name, mdnsname)
        self.assertEqual(UUT.mappings, mappings)
        self.assertEqual(UUT.port, port)
        self.assertEqual(UUT.txt_rec_base, txt_recs)
        self.assertEqual(UUT.logger, logger)

        for key in itervalues(mappings):
            self.assertIn(key, UUT.service_versions)
            self.assertEqual(UUT.service_versions[key], 0)

        UUT.mdns.register.assert_called_once_with(mdnsname, mdnstype, port, txt_recs)

    def test_p2p_enable(self):
        """Test of MDNSUpdater.p2p_enable, should trigger an mdns update"""
        mappings = {"device": "ver_dvc", "flow": "ver_flw", "source": "ver_src", "sender":"ver_snd", "receiver":"ver_rcv", "self":"ver_slf"}
        mdnstype = "_nmos-node._tcp"
        txt_recs = {"api_ver": "v1.0,v1.1,v1.2", "api_proto": "http"}
        mdnsname = "node_dummy_for_testing"
        port = 12345
        mdnsengine = mock.MagicMock()
        logger = mock.MagicMock()

        UUT = MDNSUpdater(mdnsengine, mdnstype, mdnsname, mappings, port, logger, txt_recs=txt_recs)
        UUT.P2P_enable()

        self.assertTrue(UUT.p2p_enable)
        txt_recs.update(UUT.service_versions)
        UUT.mdns.update.assert_called_once_with(mdnsname, mdnstype, txt_recs)

    def test_inc_P2P_enable_count(self):
        """Test of of MDNSUpdater.inc_P2P_enable_count, should do nothing the first p2p_cut_in_count - 1 times, and then activate P2P mode"""
        mappings = {"device": "ver_dvc", "flow": "ver_flw", "source": "ver_src", "sender":"ver_snd", "receiver":"ver_rcv", "self":"ver_slf"}
        mdnstype = "_nmos-node._tcp"
        txt_recs = {"api_ver": "v1.0,v1.1,v1.2", "api_proto": "http"}
        mdnsname = "node_dummy_for_testing"
        port = 12345
        mdnsengine = mock.MagicMock()
        logger = mock.MagicMock()

        UUT = MDNSUpdater(mdnsengine, mdnstype, mdnsname, mappings, port, logger, txt_recs=txt_recs)

        for i in range(0,UUT.p2p_cut_in_count-1):
            UUT.inc_P2P_enable_count()

            self.assertFalse(UUT.p2p_enable)
            UUT.mdns.update.assert_not_called()

        UUT.inc_P2P_enable_count()
        self.assertTrue(UUT.p2p_enable)
        txt_recs.update(UUT.service_versions)
        UUT.mdns.update.assert_called_once_with(mdnsname, mdnstype, txt_recs)

    def test_P2P_disable_when_enabled(self):
        """When an MDNSUpdater is already enabled for P2P calling P2P_disable should disable P2P"""
        mappings = {"device": "ver_dvc", "flow": "ver_flw", "source": "ver_src", "sender":"ver_snd", "receiver":"ver_rcv", "self":"ver_slf"}
        mdnstype = "_nmos-node._tcp"
        txt_recs = {"api_ver": "v1.0,v1.1,v1.2", "api_proto": "http"}
        mdnsname = "node_dummy_for_testing"
        port = 12345
        mdnsengine = mock.MagicMock()
        logger = mock.MagicMock()

        UUT = MDNSUpdater(mdnsengine, mdnstype, mdnsname, mappings, port, logger, txt_recs=txt_recs)
        UUT.P2P_enable()
        UUT.mdns.update.reset_mock()
        UUT.P2P_disable()

        self.assertFalse(UUT.p2p_enable)
        UUT.mdns.update.assert_called_once_with(mdnsname, mdnstype, txt_recs)

    def test_P2P_disable_resets_enable_count(self):
        """If an MDNSUpdater is not yet enabled for P2P but has had inc_P2P_enable_count called on it then calling P2P_disable should reset this counter."""
        mappings = {"device": "ver_dvc", "flow": "ver_flw", "source": "ver_src", "sender":"ver_snd", "receiver":"ver_rcv", "self":"ver_slf"}
        mdnstype = "_nmos-node._tcp"
        txt_recs = {"api_ver": "v1.0,v1.1,v1.2", "api_proto": "http"}
        mdnsname = "node_dummy_for_testing"
        port = 12345
        mdnsengine = mock.MagicMock()
        logger = mock.MagicMock()

        UUT = MDNSUpdater(mdnsengine, mdnstype, mdnsname, mappings, port, logger, txt_recs=txt_recs)

        for i in range(0,UUT.p2p_cut_in_count-1):
            UUT.inc_P2P_enable_count()

            self.assertFalse(UUT.p2p_enable)
            UUT.mdns.update.assert_not_called()

        UUT.P2P_disable()

        for i in range(0,UUT.p2p_cut_in_count-1):
            UUT.inc_P2P_enable_count()

            self.assertFalse(UUT.p2p_enable)
            UUT.mdns.update.assert_not_called()

        UUT.inc_P2P_enable_count()
        self.assertTrue(UUT.p2p_enable)
        txt_recs.update(UUT.service_versions)
        UUT.mdns.update.assert_called_once_with(mdnsname, mdnstype, txt_recs)

    def test_update_mdns_does_nothing_when_not_enabled(self):
        """A call to MDNSUpdater.update_mdns should not do anything if P2P is disabled"""
        mappings = {"device": "ver_dvc", "flow": "ver_flw", "source": "ver_src", "sender":"ver_snd", "receiver":"ver_rcv", "self":"ver_slf"}
        mdnstype = "_nmos-node._tcp"
        txt_recs = {"api_ver": "v1.0,v1.1,v1.2", "api_proto": "http"}
        mdnsname = "node_dummy_for_testing"
        port = 12345
        mdnsengine = mock.MagicMock()
        logger = mock.MagicMock()

        UUT = MDNSUpdater(mdnsengine, mdnstype, mdnsname, mappings, port, logger, txt_recs=txt_recs)

        UUT.update_mdns("device", "register")
        self.assertEqual(UUT.service_versions[mappings["device"]], 0)
        UUT.mdns.update.assert_not_called()

    def test_update_mdns(self):
        """A call to MDNSUpdater.update_mdns when P2P is enabled ought to call mdns.update to increment version numbers for devices. Device
        version numbers should be 8-bit integers which roll over to 0 when incremented beyond the limits of 1 byte."""
        mappings = {"device": "ver_dvc", "flow": "ver_flw", "source": "ver_src", "sender":"ver_snd", "receiver":"ver_rcv", "self":"ver_slf"}
        mdnstype = "_nmos-node._tcp"
        txt_recs = {"api_ver": "v1.0,v1.1,v1.2", "api_proto": "http"}
        mdnsname = "node_dummy_for_testing"
        port = 12345
        mdnsengine = mock.MagicMock()
        logger = mock.MagicMock()

        UUT = MDNSUpdater(mdnsengine, mdnstype, mdnsname, mappings, port, logger, txt_recs=txt_recs)
        UUT.P2P_enable()

        for i in range(1,256):
            UUT.mdns.update.reset_mock()
            UUT.update_mdns("device", "register")
            self.assertEqual(UUT.service_versions[mappings["device"]], i)
            txt_recs.update(UUT.service_versions)
            UUT.mdns.update.assert_called_once_with(mdnsname, mdnstype, txt_recs)

        UUT.mdns.update.reset_mock()
        UUT.update_mdns("device", "register")
        self.assertEqual(UUT.service_versions[mappings["device"]], 0)
        txt_recs.update(UUT.service_versions)
        UUT.mdns.update.assert_called_once_with(mdnsname, mdnstype, txt_recs)

class TestAggregator(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestAggregator, self).__init__(*args, **kwargs)
        if PY2:
            self.assertCountEqual = self.assertItemsEqual

    def setUp(self):
        paths = ['nmoscommon.aggregator.Logger',
                 'nmoscommon.aggregator.IppmDNSBridge',
                 'gevent.queue.Queue',
                 'gevent.spawn' ]
        patchers = { name : mock.patch(name) for name in paths }
        self.mocks = { name : patcher.start() for (name, patcher) in iteritems(patchers) }
        for (name, patcher) in iteritems(patchers):
            self.addCleanup(patcher.stop)

        def printmsg(t):
            def _inner(msg):
                print(t + ": " + msg)
            return _inner

#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeInfo.side_effect = printmsg("INFO")
#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeWarning.side_effect = printmsg("WARNING")
#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeDebug.side_effect = printmsg("DEBUG")
#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeError.side_effect = printmsg("ERROR")
#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeFatal.side_effect = printmsg("FATAL")

    def test_init(self):
        """Test a call to Aggregator()"""
        self.mocks['gevent.spawn'].side_effect = lambda f : mock.MagicMock(thread_function=f)

        a = Aggregator()

        self.mocks['nmoscommon.aggregator.Logger'].assert_called_once_with('aggregator_proxy', None)
        self.assertEqual(a.logger, self.mocks['nmoscommon.aggregator.Logger'].return_value)
        self.mocks['nmoscommon.aggregator.IppmDNSBridge'].assert_called_once_with(logger=a.logger)
        self.assertEqual(a._reg_queue, self.mocks['gevent.queue.Queue'].return_value)
        self.assertEqual(a.heartbeat_thread.thread_function, a._heartbeat)
        self.assertEqual(a.queue_thread.thread_function, a._process_queue)

    def test_register_into(self):
        """register_into should register an object into a namespace, adding a scheduled call to the registration queue to that effect."""
        a = Aggregator()

        objects = [
            ("dummy", "testkey", { "test_param" : "test_value", "test_param1": "test_value1" })
            ]

        for o in objects:
            a.register_into("potato", o[0], o[1], **o[2])
            a._reg_queue.put.assert_called_with({"method": "POST", "namespace": "potato", "res_type": o[0], "key": o[1]})
            send_obj = { "type" : o[0], "data" : { k : v for (k,v) in iteritems(o[2]) } }
            if 'id' not in send_obj['data']:
                send_obj['data']['id'] = o[1]
            self.assertEqual(a._registered["entities"]["potato"][o[0]][o[1]], send_obj)

    def test_register(self):
        """register should register an object into namespace "resource", adding a scheduled call to the registration queue to that effect.
        There is special behaviour when registering a node, since the object can only ever have one node registration at a time."""
        a = Aggregator()

        objects = [
            ("dummy", "testkey", { "test_param" : "test_value", "test_param1": "test_value1" }),
            ("node", "testnode", { "test_param" : "test_value", "test_param1": "test_value1" })
            ]

        for o in objects:
            a.register(o[0], o[1], **o[2])
            a._reg_queue.put.assert_called_with({"method": "POST", "namespace": "resource", "res_type": o[0], "key": o[1]})
            send_obj = { "type" : o[0], "data" : { k : v for (k,v) in iteritems(o[2]) } }
            if 'id' not in send_obj['data']:
                send_obj['data']['id'] = o[1]
            if o[0] == "node":
                self.assertEqual(a._registered["node"], send_obj)
            else:
                self.assertEqual(a._registered["entities"]["resource"][o[0]][o[1]], send_obj)

    def test_unregister(self):
        """unregister should schedule a call to unregister the specified devices.
        Special behaviour is expected when unregistering a node."""
        a = Aggregator()

        objects = [
            ("dummy", "testkey", { "test_param" : "test_value", "test_param1": "test_value1" }),
            ("node", "testnode", { "test_param" : "test_value", "test_param1": "test_value1" })
            ]

        for o in objects:
            a.register(o[0], o[1], **o[2])

        for o in objects:
            a.unregister(o[0], o[1])
            a._reg_queue.put.assert_called_with({"method": "DELETE", "namespace": "resource", "res_type":o[0], "key":o[1]})
            if o[0] == "node":
                self.assertIsNone(a._registered["node"])
            else:
                self.assertNotIn(o[1], a._registered["entities"]["resource"][o[0]])

    def test_stop(self):
        """A call to stop should set _running to false and then join the heartbeat thread."""
        self.mocks['gevent.spawn'].side_effect = lambda f : mock.MagicMock(thread_function=f)
        a = Aggregator()

        self.assertTrue(a._running)

        a.stop()

        self.assertFalse(a._running)
        a.heartbeat_thread.join.assert_called_with()
        a.queue_thread.join.assert_called_with()

    def test_heartbeat_registers(self):
        """The heartbeat thread should trigger a registration of the node if the node is not yet registered when it is run."""
        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = False

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop):
            with mock.patch.object(a, '_process_reregister') as procreg:
                with mock.patch.object(a, '_SEND') as SEND:
                    a._heartbeat()
                    procreg.assert_called_with()
                    SEND.assert_not_called()
                    a._mdns_updater.inc_P2P_enable_count.assert_not_called()

    def test_heartbeat_unregisters_when_no_node(self):
        """Each time the heartbeat thread finds there is no node it should mark the object as unregistered and increment the P2P enable count."""
        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = None

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop):
            with mock.patch.object(a, '_process_reregister') as procreg:
                with mock.patch.object(a, '_SEND') as SEND:
                    a._heartbeat()
                    procreg.assert_not_called()
                    SEND.assert_not_called()
                    a._mdns_updater.inc_P2P_enable_count.assert_called_with()
                    self.assertFalse(a._registered["registered"])

    def test_heartbeat_correctly(self):
        """Each time the heartbeat thread activates if there is already a registered node then it should trigger a SEND of a heartbeat."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop):
            with mock.patch.object(a, '_process_reregister') as procreg:
                with mock.patch.object(a, '_SEND') as SEND:
                    a._heartbeat()

                    procreg.assert_not_called()
                    SEND.assert_called_with("POST", "/health/nodes/" + DUMMYNODEID)
                    a._mdns_updater.inc_P2P_enable_count.assert_not_called()
                    self.assertTrue(a._registered["registered"])

    def test_heartbeat_with_404_exception(self):
        """If the heartbeat returns a 404 exception then the object should reset to unregistered state and increment the P2P enable counter."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop):
            with mock.patch.object(a, '_process_reregister') as procreg:
                with mock.patch.object(a, '_SEND', side_effect=InvalidRequest(status_code=404)) as SEND:
                    a._heartbeat()

                    procreg.assert_not_called()
                    SEND.assert_called_with("POST", "/health/nodes/" + DUMMYNODEID)
                    a._mdns_updater.inc_P2P_enable_count.assert_called_with()
                    self.assertFalse(a._registered["registered"])

    def test_heartbeat_with_500_exception(self):
        """If the heartbeat returns a 500 exception then the object should simply exit. This is a bad way."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop) as sleep:
            with mock.patch.object(a, '_process_reregister') as procreg:
                with mock.patch.object(a, '_SEND', side_effect=InvalidRequest(status_code=500)) as SEND:
                    a._heartbeat()

                    procreg.assert_not_called()
                    SEND.assert_called_with("POST", "/health/nodes/" + DUMMYNODEID)
                    a._mdns_updater.inc_P2P_enable_count.assert_not_called()
                    sleep.assert_not_called()

    def test_heartbeat_with_other_exception(self):
        """If an unknown exception is raised during the heartbeat process then the object should reset to unregistered state but not increment the P2P enable counter."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop):
            with mock.patch.object(a, '_process_reregister') as procreg:
                with mock.patch.object(a, '_SEND', side_effect=Exception) as SEND:
                    a._heartbeat()

                    procreg.assert_not_called()
                    SEND.assert_called_with("POST", "/health/nodes/" + DUMMYNODEID)
                    a._mdns_updater.inc_P2P_enable_count.assert_not_called()
                    self.assertFalse(a._registered["registered"])

    def test_process_queue_does_nothing_when_not_registered(self):
        """The queue processing thread should not SEND any messages when the node is not registered."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = False
        a._reg_queue.empty.return_value = True

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop) as sleep:
            with mock.patch.object(a, '_SEND') as SEND:
                a._process_queue()

                SEND.assert_not_called()
                a._mdns_updater.P2P_disable.assert_not_called()
                sleep.assert_called_with(mock.ANY)

    def test_process_queue_does_nothing_when_queue_empty(self):
        """The queue processing thread should not SEND any messages when the queue is empty."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }
        a._reg_queue.empty.return_value = True

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop) as sleep:
            with mock.patch.object(a, '_SEND') as SEND:
                a._process_queue()

                SEND.assert_not_called()
                a._mdns_updater.P2P_disable.assert_not_called()
                sleep.assert_called_with(mock.ANY)

    def test_process_queue_processes_queue_when_running(self):
        """The queue processing thread should check the queue and SEND a registration/deregistration request to the remote aggregator when required."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        DUMMYKEY = "dummykey"
        DUMMYPARAMKEY = "dummyparamkey"
        DUMMYPARAMVAL = "dummyparamval"

        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }
        if "entities" not in a._registered:
            a._registered["entities"] = {}
        if "resource" not in a._registered["entities"]:
            a._registered["entities"]["resource"] = {}
        if "dummy" not in a._registered["entities"]["resource"]:
            a._registered["entities"]["resource"]["dummy"] = {}
        a._registered["entities"]["resource"]["dummy"][DUMMYKEY] = { DUMMYPARAMKEY : DUMMYPARAMVAL }

        queue = [
            { "method": "POST", "namespace": "resource", "res_type": "node", "key": DUMMYNODEID },
            { "method": "POST", "namespace": "resource", "res_type": "dummy", "key": DUMMYKEY },
            { "method": "DELETE", "namespace": "resource", "res_type": "dummy", "key": DUMMYKEY }
            ]

        a._reg_queue.empty.side_effect = lambda : (len(queue) == 0)
        a._reg_queue.get.side_effect = lambda : queue.pop(0)

        expected_calls = [
            mock.call('POST', '/resource', a._registered["node"]),
            mock.call('POST', '/health/nodes/' + DUMMYNODEID),
            mock.call('POST', '/resource', a._registered["entities"]["resource"]["dummy"][DUMMYKEY]),
            mock.call('DELETE', '/resource/dummys/' + DUMMYKEY)
            ]

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop) as sleep:
            with mock.patch.object(a, '_SEND') as SEND:
                a._process_queue()

                SEND.assert_has_calls(expected_calls)
                a._mdns_updater.P2P_disable.assert_called_with()

    def test_process_queue_processes_queue_when_not_running(self):
        """The process queue method should continue until the queue is empty even if the object has been instructed to stop. Then it should stop only once the queue is empty."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        DUMMYKEY = "dummykey"
        DUMMYPARAMKEY = "dummyparamkey"
        DUMMYPARAMVAL = "dummyparamval"

        a = Aggregator(mdns_updater=mock.MagicMock())
        a._running = False
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }
        if "entities" not in a._registered:
            a._registered["entities"] = {}
        if "resource" not in a._registered["entities"]:
            a._registered["entities"]["resource"] = {}
        if "dummy" not in a._registered["entities"]["resource"]:
            a._registered["entities"]["resource"]["dummy"] = {}
        a._registered["entities"]["resource"]["dummy"][DUMMYKEY] = { DUMMYPARAMKEY : DUMMYPARAMVAL }

        queue = [
            { "method": "POST", "namespace": "resource", "res_type": "node", "key": DUMMYNODEID },
            { "method": "POST", "namespace": "resource", "res_type": "dummy", "key": DUMMYKEY },
            { "method": "DELETE", "namespace": "resource", "res_type": "dummy", "key": DUMMYKEY }
            ]

        a._reg_queue.empty.side_effect = lambda : (len(queue) == 0)
        a._reg_queue.get.side_effect = lambda : queue.pop(0)

        expected_calls = [
            mock.call('POST', '/resource', a._registered["node"]),
            mock.call('POST', '/health/nodes/' + DUMMYNODEID),
            mock.call('POST', '/resource', a._registered["entities"]["resource"]["dummy"][DUMMYKEY]),
            mock.call('DELETE', '/resource/dummys/' + DUMMYKEY)
            ]

        with mock.patch('gevent.sleep', side_effect=Exception) as sleep:
            with mock.patch.object(a, '_SEND') as SEND:
                try:
                    a._process_queue()
                except:
                    self.fail(msg="process_queue kept running")

                SEND.assert_has_calls(expected_calls)
                a._mdns_updater.P2P_disable.assert_called_with()
                sleep.assert_not_called()

    def test_process_queue_processes_queue_when_running_and_aborts_on_exception_in_node_register(self):
        """If a node register performed by the queue processing thread throws an exception then the loop should abort."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        DUMMYKEY = "dummykey"
        DUMMYPARAMKEY = "dummyparamkey"
        DUMMYPARAMVAL = "dummyparamval"

        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }
        if "entities" not in a._registered:
            a._registered["entities"] = {}
        if "resource" not in a._registered["entities"]:
            a._registered["entities"]["resource"] = {}
        if "dummy" not in a._registered["entities"]["resource"]:
            a._registered["entities"]["resource"]["dummy"] = {}
        a._registered["entities"]["resource"]["dummy"][DUMMYKEY] = { DUMMYPARAMKEY : DUMMYPARAMVAL }

        queue = [
            { "method": "POST", "namespace": "resource", "res_type": "node", "key": DUMMYNODEID },
            ]

        a._reg_queue.empty.side_effect = lambda : (len(queue) == 0)
        a._reg_queue.get.side_effect = lambda : queue.pop(0)

        expected_calls = [
            mock.call('POST', '/resource', a._registered["node"]),
            ]

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop) as sleep:
            with mock.patch.object(a, '_SEND', side_effect=Exception) as SEND:
                a._process_queue()

                SEND.assert_has_calls(expected_calls)
                a._mdns_updater.P2P_disable.assert_not_called()

    def test_process_queue_processes_queue_when_running_and_aborts_on_exception_in_general_register(self):
        """If a non-node register performed by the queue processing thread throws an exception then the loop should abort."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        DUMMYKEY = "dummykey"
        DUMMYPARAMKEY = "dummyparamkey"
        DUMMYPARAMVAL = "dummyparamval"

        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }
        if "entities" not in a._registered:
            a._registered["entities"] = {}
        if "resource" not in a._registered["entities"]:
            a._registered["entities"]["resource"] = {}
        if "dummy" not in a._registered["entities"]["resource"]:
            a._registered["entities"]["resource"]["dummy"] = {}
        a._registered["entities"]["resource"]["dummy"][DUMMYKEY] = { DUMMYPARAMKEY : DUMMYPARAMVAL }

        queue = [
            { "method": "POST", "namespace": "resource", "res_type": "dummy", "key": DUMMYKEY },
            ]

        a._reg_queue.empty.side_effect = lambda : (len(queue) == 0)
        a._reg_queue.get.side_effect = lambda : queue.pop(0)

        expected_calls = [
            mock.call('POST', '/resource', a._registered["entities"]["resource"]["dummy"][DUMMYKEY]),
            ]

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop) as sleep:
            with mock.patch.object(a, '_SEND', side_effect=InvalidRequest) as SEND:
                a._process_queue()

                SEND.assert_has_calls(expected_calls)
                a._mdns_updater.P2P_disable.assert_not_called()
                self.assertNotIn(DUMMYKEY, a._registered["entities"]["resource"]["dummy"])

    def test_process_queue_processes_queue_when_running_and_aborts_on_exception_in_general_unregister(self):
        """If an unregister performed by the queue processing thread throws an exception then the loop should abort."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        DUMMYKEY = "dummykey"
        DUMMYPARAMKEY = "dummyparamkey"
        DUMMYPARAMVAL = "dummyparamval"

        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }
        if "entities" not in a._registered:
            a._registered["entities"] = {}
        if "resource" not in a._registered["entities"]:
            a._registered["entities"]["resource"] = {}
        if "dummy" not in a._registered["entities"]["resource"]:
            a._registered["entities"]["resource"]["dummy"] = {}
        a._registered["entities"]["resource"]["dummy"][DUMMYKEY] = { DUMMYPARAMKEY : DUMMYPARAMVAL }

        queue = [
            { "method": "DELETE", "namespace": "resource", "res_type": "dummy", "key": DUMMYKEY }
            ]

        a._reg_queue.empty.side_effect = lambda : (len(queue) == 0)
        a._reg_queue.get.side_effect = lambda : queue.pop(0)

        expected_calls = [
            mock.call('DELETE', '/resource/dummys/' + DUMMYKEY),
            ]

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop) as sleep:
            with mock.patch.object(a, '_SEND', side_effect=InvalidRequest) as SEND:
                a._process_queue()

                SEND.assert_has_calls(expected_calls)
                a._mdns_updater.P2P_disable.assert_not_called()

    def test_process_queue_processes_queue_when_running_and_ignores_unknown_methods(self):
        """Unknown verbs in the queue should be ignored."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        DUMMYKEY = "dummykey"
        DUMMYPARAMKEY = "dummyparamkey"
        DUMMYPARAMVAL = "dummyparamval"

        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }
        if "entities" not in a._registered:
            a._registered["entities"] = {}
        if "resource" not in a._registered["entities"]:
            a._registered["entities"]["resource"] = {}
        if "dummy" not in a._registered["entities"]["resource"]:
            a._registered["entities"]["resource"]["dummy"] = {}
        a._registered["entities"]["resource"]["dummy"][DUMMYKEY] = { DUMMYPARAMKEY : DUMMYPARAMVAL }

        queue = [
            { "method": "DANCE", "namespace": "resource", "res_type": "dummy", "key": DUMMYKEY }
            ]

        a._reg_queue.empty.side_effect = lambda : (len(queue) == 0)
        a._reg_queue.get.side_effect = lambda : queue.pop(0)

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop) as sleep:
            with mock.patch.object(a, '_SEND', side_effect=InvalidRequest) as SEND:
                a._process_queue()

                SEND.assert_not_called()
                a._mdns_updater.P2P_disable.assert_not_called()

    def test_process_queue_handles_exception_in_unqueueing(self):
        """An exception in unqueing an item should reset the object state to unregistered."""
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        DUMMYKEY = "dummykey"
        DUMMYPARAMKEY = "dummyparamkey"
        DUMMYPARAMVAL = "dummyparamval"

        a = Aggregator(mdns_updater=mock.MagicMock())
        a._registered["registered"] = True

        a._reg_queue.empty.return_value = False
        a._reg_queue.get.side_effect = Exception

        def killloop(*args, **kwargs):
            a._running = False

        with mock.patch('gevent.sleep', side_effect=killloop) as sleep:
            with mock.patch.object(a, '_SEND') as SEND:
                a._process_queue()

                SEND.assert_not_called()
                a._mdns_updater.P2P_disable.assert_called_with()
                self.assertFalse(a._registered["registered"])




    # In order to test the _process_reregister method we define some extra infrastructure

    # These are the steps that the method passes through before completing, it is possible for it to fail early
    REREGISTER_START       = 0
    REREGISTER_DELETE      = 1
    REREGISTER_INC_PTP     = 2
    REREGISTER_QUEUE_DRAIN = 3
    REREGISTER_NODE        = 4
    REREGISTER_RESOURCES   = 5
    REREGISTER_COMPLETE    = 6

    def assert_reregister_runs_correctly(self, _send=None, to_point=REREGISTER_COMPLETE, with_prerun=None, trigger_exception_in_drain=False):
        """This method is used to assert that the _process_reregister method runs to the specified point. The other parameters
        allow the test conditions to be varied.
        _send is a side-effect which will be applied whenever the _SEND method is called.
        with_prerun can be set to a callable which takes the aggregator object as a single parameter and is called just before
        a._process_reregister is.
        """
        DUMMYNODEID = "90f7c2c0-cfa9-11e7-9b9d-2fe338e1e7ce"
        DUMMYKEY = "dummykey"
        DUMMYPARAMKEY = "dummyparamkey"
        DUMMYPARAMVAL = "dummyparamval"
        DUMMYFLOW = "dummyflow"
        DUMMYDEVICE = "dummydevice"

        a = Aggregator(mdns_updater=mock.MagicMock())
        a._running = True
        a._registered["registered"] = True
        a._registered["node"] = { "type" : "node", "data" : { "id" : DUMMYNODEID } }
        if "entities" not in a._registered:
            a._registered["entities"] = {}
        if "resource" not in a._registered["entities"]:
            a._registered["entities"]["resource"] = {}
        if "dummy" not in a._registered["entities"]["resource"]:
            a._registered["entities"]["resource"]["dummy"] = {}
        if "device" not in a._registered["entities"]["resource"]:
            a._registered["entities"]["resource"]["device"] = {}
        if "flow" not in a._registered["entities"]["resource"]:
            a._registered["entities"]["resource"]["flow"] = {}
        a._registered["entities"]["resource"]["dummy"][DUMMYKEY]     = { DUMMYPARAMKEY : DUMMYPARAMVAL }
        a._registered["entities"]["resource"]["device"][DUMMYDEVICE] = { DUMMYPARAMKEY : DUMMYPARAMVAL }
        a._registered["entities"]["resource"]["flow"][DUMMYFLOW]     = { DUMMYPARAMKEY : DUMMYPARAMVAL }

        queue = starting_queue = [
            { "method": "POST",   "namespace": "resource", "res_type": "dummy", "key": DUMMYKEY },
            { "method": "DELETE", "namespace": "resource", "res_type": "dummy", "key": DUMMYKEY }
            ]

        a._reg_queue.empty.side_effect = lambda : (len(queue) == 0)
        class SpecialEmptyQueueException (Exception):
            pass
        gevent.queue.Queue.Empty = SpecialEmptyQueueException
        def _get(block=True):
            if len(queue) == 0 or trigger_exception_in_drain:
                while len(queue) > 0:
                    queue.pop(0)
                raise gevent.queue.Queue.Empty
            return queue.pop(0)
        a._reg_queue.get.side_effect = _get

        expected_send_calls = []
        if to_point >= self.REREGISTER_DELETE:
            expected_send_calls += [
                mock.call("DELETE", "/resource/nodes/" + a._registered["node"]["data"]["id"]),
                ]
        if to_point >= self.REREGISTER_NODE:
            expected_send_calls += [
                mock.call('POST', '/resource', a._registered["node"]),
                ]
        if to_point > self.REREGISTER_NODE:
            expected_send_calls += [
                mock.call('POST', '/health/nodes/' + DUMMYNODEID)
            ]

        expected_put_calls = []
        if to_point >= self.REREGISTER_RESOURCES:
            # The reregistration of the other resources should be queued for the next run loop, and arranged in order
            expected_put_calls = (
                sum([
                    [ mock.call({ "method": "POST",   "namespace": "resource", "res_type": res_type, "key": key }) for key in a._registered["entities"]["resource"][res_type] ]
                    for res_type in a.registration_order if res_type in a._registered["entities"]["resource"]
                    ], []) +
                sum([
                    [ mock.call({ "method": "POST",   "namespace": "resource", "res_type": res_type, "key": key }) for key in a._registered["entities"]["resource"][res_type] ]
                    for res_type in a._registered["entities"]["resource"] if res_type not in a.registration_order
                    ], [])
                )

        with mock.patch.object(a, '_SEND', side_effect=_send) as SEND:
            if with_prerun is not None:
                with_prerun(a)
            a._process_reregister()

            self.assertCountEqual(SEND.mock_calls, expected_send_calls)
            if to_point >= self.REREGISTER_INC_PTP:
                a._mdns_updater.inc_P2P_enable_count.assert_called_with()
            else:
                a._mdns_updater.inc_P2P_enable_count.assert_not_called()
            if to_point >= self.REREGISTER_QUEUE_DRAIN:
                self.assertListEqual(queue, [])
            else:
                self.assertListEqual(queue, starting_queue)
            if to_point > self.REREGISTER_NODE:
                a._mdns_updater.P2P_disable.assert_called_with()
            else:
                a._mdns_updater.P2P_disable.assert_not_called()
            self.assertListEqual(a._reg_queue.put.mock_calls, expected_put_calls)

    def test_process_reregister(self):
        """A call to process_reregister with no errors should delete the current registration, increment the P2P enable counter, drain the queue, reregister the node, and then reregister the resources."""
        self.assert_reregister_runs_correctly()

    def test_process_reregister_handles_queue_exception(self):
        """A call to process_reregister where the queue drain raises an exception should still delete the current registration, increment the P2P enable counter, drain the queue, reregister the node, and then reregister the resources."""
        self.assert_reregister_runs_correctly(trigger_exception_in_drain=True)

    def test_process_reregister_bails_if_node_not_registered(self):
        """A call to process_reregister where the node is not registered should bail at the start."""
        def _prerun(a):
            a._registered["registered"] = False
            a._registered["node"] = None

        self.assert_reregister_runs_correctly(to_point=self.REREGISTER_START, with_prerun=_prerun)

    def test_process_reregister_continues_when_delete_fails(self):
        """A call to process_reregister where the DELETE call returns 404 should still delete the current registration, increment the P2P enable counter, drain the queue, reregister the node, and then reregister the resources."""
        def _send(method, path, data=None):
            if method == "DELETE":
                raise InvalidRequest(status_code=404)
            else:
                return
        self.assert_reregister_runs_correctly(_send=_send)

    def test_process_reregister_bails_if_delete_throws_unknown_exception(self):
        """A call to process_reregister where DELETE message throws an unknown exception should delete the current registration, then bail"""
        def _send(method, path, data=None):
            if method == "DELETE":
                raise Exception
            else:
                return
        self.assert_reregister_runs_correctly(_send=_send, to_point=self.REREGISTER_DELETE)

    def test_process_reregister_bails_if_first_post_throws_unknown_exception(self):
        """A call to process_reregister where the POST call raises an exception should still delete the current registration, increment the P2P enable counter, drain the queue, and try to reregister the node, but should bail before reregistering the resources."""
        def _send(method, path, data=None):
            if method == "POST":
                raise Exception
            else:
                return
        self.assert_reregister_runs_correctly(_send=_send, to_point=self.REREGISTER_NODE)


    #testing the _SEND method is similarly complex
    SEND_START                    = 0
    SEND_AGGREGATOR_EMPTY_CHECK_0 = 1
    SEND_ITERATION_0              = 2
    SEND_AGGREGATOR_EMPTY_CHECK_1 = 3
    SEND_ITERATION_1              = 4
    SEND_AGGREGATOR_EMPTY_CHECK_2 = 5
    SEND_ITERATION_2              = 6
    SEND_TOO_MANY_RETRIES         = 7

    def assert_send_runs_correctly(self, method, url, data=None, headers=None, to_point=SEND_ITERATION_0, initial_aggregator="", aggregator_urls=["http://example0.com/aggregator/", "http://example1.com/aggregator/", "http://example2.com/aggregator/"], request=None, expected_return=None, expected_exception=None, prefer_ipv6=False):
        """This method checks that the SEND routine runs through its state machine as expected:

        The states are:

    SEND_START                    = The start of the method
    SEND_AGGREGATOR_EMPTY_CHECK_0 = Check that the aggregator value href isn't empty
    SEND_ITERATION_0              = Attempt a SEND
    SEND_AGGREGATOR_EMPTY_CHECK_1 = Check that the aggregator value href isn't empty
    SEND_ITERATION_1              = Attempt a SEND
    SEND_AGGREGATOR_EMPTY_CHECK_2 = Check that the aggregator value href isn't empty
    SEND_ITERATION_2              = Attempt a SEND
    SEND_TOO_MANY_RETRIES         = Raise an exception due to too many failures.

    If any of the SEND attempts succeeds then the routine exits immediately succesfully.
"""
        aggregator_urls_queue = [ x for x in aggregator_urls ]
        def _get_href(_):
            if len(aggregator_urls_queue) == 0:
                return ""
            else:
                return aggregator_urls_queue.pop(0)

        a = Aggregator(mdns_updater=mock.MagicMock())
        a.mdnsbridge.getHref.side_effect = _get_href
        a.aggregator=initial_aggregator

        expected_gethref_calls = []
        if initial_aggregator == "":
            expected_gethref_calls.append(mock.call(REGISTRATION_MDNSTYPE))

        if data is not None:
            expected_data = json.dumps(data)
        else:
            expected_data = None

        while len(aggregator_urls) < 3:
            aggregator_urls.append("")

        expected_request_calls = []
        if to_point >= self.SEND_ITERATION_0:
            if not prefer_ipv6:
                expected_request_calls.append(mock.call(method, urljoin(aggregator_urls[0], AGGREGATOR_APINAMESPACE + "/" + AGGREGATOR_APINAME + "/" + AGGREGATOR_APIVERSION + url), data=expected_data, headers=headers, timeout=1.0))
            else:
                expected_request_calls.append(mock.call(method, urljoin(aggregator_urls[0], AGGREGATOR_APINAMESPACE + "/" + AGGREGATOR_APINAME + "/" + AGGREGATOR_APIVERSION + url), data=expected_data, headers=headers, timeout=1.0, proxies={'http':''}))
        if to_point > self.SEND_ITERATION_0:
            expected_gethref_calls.append(mock.call(REGISTRATION_MDNSTYPE))
        if to_point >= self.SEND_ITERATION_1:
            if not prefer_ipv6:
                expected_request_calls.append(mock.call(method, urljoin(aggregator_urls[1], AGGREGATOR_APINAMESPACE + "/" + AGGREGATOR_APINAME + "/" + AGGREGATOR_APIVERSION + url), data=expected_data, headers=headers, timeout=1.0))
            else:
                expected_request_calls.append(mock.call(method, urljoin(aggregator_urls[1], AGGREGATOR_APINAMESPACE + "/" + AGGREGATOR_APINAME + "/" + AGGREGATOR_APIVERSION + url), data=expected_data, headers=headers, timeout=1.0, proxies={'http':''}))
        if to_point > self.SEND_ITERATION_1:
            expected_gethref_calls.append(mock.call(REGISTRATION_MDNSTYPE))
        if to_point >= self.SEND_ITERATION_2:
            if not prefer_ipv6:
                expected_request_calls.append(mock.call(method, urljoin(aggregator_urls[2], AGGREGATOR_APINAMESPACE + "/" + AGGREGATOR_APINAME + "/" + AGGREGATOR_APIVERSION + url), data=expected_data, headers=headers, timeout=1.0))
            else:
                expected_request_calls.append(mock.call(method, urljoin(aggregator_urls[2], AGGREGATOR_APINAMESPACE + "/" + AGGREGATOR_APINAME + "/" + AGGREGATOR_APIVERSION + url), data=expected_data, headers=headers, timeout=1.0, proxies={'http':''}))
        if to_point > self.SEND_ITERATION_2:
            expected_gethref_calls.append(mock.call(REGISTRATION_MDNSTYPE))

        if to_point in (self.SEND_AGGREGATOR_EMPTY_CHECK_0, self.SEND_AGGREGATOR_EMPTY_CHECK_1, self.SEND_AGGREGATOR_EMPTY_CHECK_2):
            expected_exception = NoAggregator
        elif to_point == self.SEND_TOO_MANY_RETRIES:
            expected_exception = TooManyRetries

        with mock.patch.dict(nmoscommon.aggregator.nmoscommonconfig.config, { 'prefer_ipv6' : prefer_ipv6 }):
            with mock.patch("requests.request", side_effect=request) as _request:
                R = None
                if expected_exception is not None:
                    with self.assertRaises(expected_exception):
                        R = a._SEND(method, url, data)
                else:
                    try:
                        R = a._SEND(method, url, data)
                    except Exception as e:
                        self.fail(msg="_SEND threw an unexpected exception, %s" % (traceback.format_exception(e)))

                self.assertListEqual(a.mdnsbridge.getHref.mock_calls, expected_gethref_calls)
                self.assertListEqual(_request.mock_calls, expected_request_calls)
                self.assertEqual(R, expected_return)

    def test_send_get_with_no_aggregators_fails_at_first_checkpoint(self):
        """If there are no aggregators then the SEND method will fail immediately"""
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_AGGREGATOR_EMPTY_CHECK_0, aggregator_urls=[])

    def test_send_get_which_returns_400_raises_exception(self):
        """If the first attempt at sending gives a 400 error then the SEND method will raise it."""
        def request(*args, **kwargs):
            return mock.MagicMock(status_code = 400)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_0, request=request, expected_exception=InvalidRequest)

    def test_send_get_which_returns_204_returns_nothing(self):
        """If the first attempt at sending gives a 204 success then the SEND method will return normally."""
        def request(*args, **kwargs):
            return mock.MagicMock(status_code = 204)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_0, request=request, expected_return=None)

    def test_send_put_which_returns_204_returns_nothing(self):
        """If the first attempt at sending gives a 204 success then the SEND method will return normally."""
        data = { "dummy0" : "dummy1",
                     "dummy2" : [ "dummy3", "dummy4" ] }
        def request(*args, **kwargs):
            return mock.MagicMock(status_code = 204)
        self.assert_send_runs_correctly("PUT", "/dummy/url", data=data, headers={"Content-Type": "application/json"}, to_point=self.SEND_ITERATION_0, request=request, expected_return=None)

    def test_send_get_which_returns_200_returns_content(self):
        """If the first attempt at sending gives a 200 success then the SEND method will return normally with a body."""
        TEST_CONTENT = "kasjhdlkhnjgsnhjhgwhudjdndjhnrhg;kduhjhnf"
        def request(*args, **kwargs):
            return mock.MagicMock(status_code = 200, headers={}, content=TEST_CONTENT)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_0, request=request, expected_return=TEST_CONTENT)

    def test_send_over_ipv6_get_which_returns_200_returns_content(self):
        """If the first attempt at sending gives a 200 success then the SEND method will return normally with a body over ipv6."""
        TEST_CONTENT = "kasjhdlkhnjgsnhjhgwhudjdndjhnrhg;kduhjhnf"
        def request(*args, **kwargs):
            return mock.MagicMock(status_code = 200, headers={}, content=TEST_CONTENT)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_0, request=request, expected_return=TEST_CONTENT, prefer_ipv6 = True)

    def test_send_get_which_returns_201_returns_content(self):
        """If the first attempt at sending gives a 201 success then the SEND method will return normally with a body."""
        TEST_CONTENT = "kasjhdlkhnjgsnhjhgwhudjdndjhnrhg;kduhjhnf"
        def request(*args, **kwargs):
            return mock.MagicMock(status_code = 201, headers={}, content=TEST_CONTENT)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_0, request=request, expected_return=TEST_CONTENT)

    def test_send_get_which_returns_200_and_json_returns_json(self):
        """If the first attempt at sending gives a 200 success then the SEND method will return normally and decode the body as json."""
        TEST_CONTENT = { "foo" : "bar",
                             "baz" : [ "potato", "sundae" ] }
        def request(*args, **kwargs):
            return mock.MagicMock(status_code = 200, headers={"content-type" : "application/json"}, json=mock.MagicMock(return_value=TEST_CONTENT))
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_0, request=request, expected_return=TEST_CONTENT)

    def test_send_get_which_fails_with_only_one_aggregator_fails_at_second_checkpoint(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href, if it fails it will fail."""
        def request(*args, **kwargs):
            return None
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_AGGREGATOR_EMPTY_CHECK_1, request=request, aggregator_urls=["http://example.com/aggregator/",])

    def test_send_get_which_raises_with_only_one_aggregator_fails_at_second_checkpoint(self):
        """If the first attempt at sending throws an Exception then the SEND routine will try to get an alternative href, if it fails it will fail."""
        def request(*args, **kwargs):
            raise requests.exceptions.RequestException
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_AGGREGATOR_EMPTY_CHECK_1, request=request, aggregator_urls=["http://example.com/aggregator/",])

    def test_send_get_which_returns_500_with_only_one_aggregator_fails_at_second_checkpoint(self):
        """If the first attempt at sending returns a 500 error then the SEND routine will try to get an alternative href, if it fails it will fail."""
        def request(*args, **kwargs):
            return mock.MagicMock(status_code = 500)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_AGGREGATOR_EMPTY_CHECK_1, request=request, aggregator_urls=["http://example.com/aggregator/",])

    def test_send_get_which_fails_then_returns_400_raises_exception(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt returns a 400 then it will raise an Exception"""
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls == 1:
                return None
            else:
                return mock.MagicMock(status_code = 400)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_1, request=request, expected_exception=InvalidRequest)

    def test_send_get_which_fails_then_returns_204_returns_nothing(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt returns a 204 then it will return normally."""
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls == 1:
                return None
            else:
                return mock.MagicMock(status_code = 204)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_1, request=request, expected_return=None)

    def test_send_get_which_fails_then_returns_200_returns_content(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt returns a 200 then it will return the body sent back by the remote aggregator"""
        TEST_CONTENT = "kasjhdlkhnjgsnhjhgwhudjdndjhnrhg;kduhjhnf"
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls == 1:
                return None
            else:
                return mock.MagicMock(status_code = 200, headers={}, content=TEST_CONTENT)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_1, request=request, expected_return=TEST_CONTENT)

    def test_send_get_which_fails_then_returns_201_returns_content(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt returns a 201 then it will return the body sent back by the remote aggregator"""
        TEST_CONTENT = "kasjhdlkhnjgsnhjhgwhudjdndjhnrhg;kduhjhnf"
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls == 1:
                return None
            else:
                return mock.MagicMock(status_code = 201, headers={}, content=TEST_CONTENT)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_1, request=request, expected_return=TEST_CONTENT)

    def test_send_get_which_fails_then_returns_200_and_json_returns_content(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt returns a 200 with Content-Type as application/json then it will return the body sent back by the remote aggregator decoded as json"""
        TEST_CONTENT = { "foo" : "bar",
                             "baz" : [ "potato", "sundae" ] }
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls == 1:
                return None
            else:
                return mock.MagicMock(status_code = 200, headers={"content-type" : "application/json"}, json=mock.MagicMock(return_value=TEST_CONTENT))
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_1, request=request, expected_return=TEST_CONTENT)

    def test_send_get_which_fails_with_only_two_aggregators_fails_at_third_checkpoint(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt at sending times out then the SEND routine will try to get an alternative href.
        If it fails then the call fails."""
        def request(*args, **kwargs):
            return None
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_AGGREGATOR_EMPTY_CHECK_2, request=request, aggregator_urls=["http://example.com/aggregator/", "http://example1.com/aggregator/"])

    def test_send_get_which_fails_twice_then_returns_400_raises_exception(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt at sending times out then the SEND routine will try to get an alternative href.
        If the third attempt returns a 400 then it raiases an exception."""
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls < 3:
                return None
            else:
                return mock.MagicMock(status_code = 400)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_2, request=request, expected_exception=InvalidRequest)

    def test_send_get_which_fails_twice_then_returns_204_returns_nothing(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt at sending times out then the SEND routine will try to get an alternative href.
        If the third attempt returns a 204 then it returns normally."""
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls < 3:
                return None
            else:
                return mock.MagicMock(status_code = 204)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_2, request=request, expected_return=None)

    def test_send_get_which_fails_twice_then_returns_200_returns_content(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt at sending times out then the SEND routine will try to get an alternative href.
        If the third attempt returns a 200 then it returns the body sent back."""
        TEST_CONTENT = "kasjhdlkhnjgsnhjhgwhudjdndjhnrhg;kduhjhnf"
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls < 3:
                return None
            else:
                return mock.MagicMock(status_code = 200, headers={}, content=TEST_CONTENT)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_2, request=request, expected_return=TEST_CONTENT)

    def test_send_get_which_fails_twice_then_returns_201_returns_content(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt at sending times out then the SEND routine will try to get an alternative href.
        If the third attempt returns a 201 then it returns the body sent back."""
        TEST_CONTENT = "kasjhdlkhnjgsnhjhgwhudjdndjhnrhg;kduhjhnf"
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls < 3:
                return None
            else:
                return mock.MagicMock(status_code = 201, headers={}, content=TEST_CONTENT)
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_2, request=request, expected_return=TEST_CONTENT)

    def test_send_get_which_fails_twice_then_returns_200_and_json_returns_content(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt at sending times out then the SEND routine will try to get an alternative href.
        If the third attempt returns a 200 with Content-Type as application/json then it returns the body sent back decoded as json."""
        TEST_CONTENT = { "foo" : "bar",
                             "baz" : [ "potato", "sundae" ] }
        class scoper:
            num_calls = 0
        def request(*args, **kwargs):
            scoper.num_calls += 1
            if scoper.num_calls < 3:
                return None
            else:
                return mock.MagicMock(status_code = 200, headers={"content-type" : "application/json"}, json=mock.MagicMock(return_value=TEST_CONTENT))
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_ITERATION_2, request=request, expected_return=TEST_CONTENT)

    def test_send_get_which_fails_on_three_aggregators_raises(self):
        """If the first attempt at sending times out then the SEND routine will try to get an alternative href.
        If the second attempt at sending times out then the SEND routine will try to get an alternative href.
        If the third attempt at sending times out then the SEND routine will fail."""
        def request(*args, **kwargs):
            return None
        self.assert_send_runs_correctly("GET", "/dummy/url", to_point=self.SEND_TOO_MANY_RETRIES, request=request)

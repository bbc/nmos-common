import unittest
import mock
from nmoscommon.aggregator import *
import nmoscommon.logger


class TestAggregator(unittest.TestCase):
    def setUp(self):
        paths = ['nmoscommon.aggregator.Logger',
                 'nmoscommon.aggregator.IppmDNSBridge',
                 'gevent.queue.Queue',
                 'gevent.spawn' ]
        patchers = { name : mock.patch(name) for name in paths }
        self.mocks = { name : patcher.start() for (name, patcher) in patchers.iteritems() }
        for (name, patcher) in patchers.iteritems():
            self.addCleanup(patcher.stop)

        def printmsg(t):
            def _inner(msg):
                print t + ": " + msg
            return _inner

#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeInfo.side_effect = printmsg("INFO")
#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeWarning.side_effect = printmsg("WARNING")
#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeDebug.side_effect = printmsg("DEBUG")
#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeError.side_effect = printmsg("ERROR")
#        self.mocks['nmoscommon.aggregator.Logger'].return_value.writeFatal.side_effect = printmsg("FATAL")
    
    def test_init(self):
        self.mocks['gevent.spawn'].side_effect = lambda f : mock.MagicMock(thread_function=f)

        a = Aggregator()

        self.mocks['nmoscommon.aggregator.Logger'].assert_called_once_with('aggregator_proxy', None)
        self.assertEqual(a.logger, self.mocks['nmoscommon.aggregator.Logger'].return_value)
        self.mocks['nmoscommon.aggregator.IppmDNSBridge'].assert_called_once_with(logger=a.logger)
        self.assertEqual(a._reg_queue, self.mocks['gevent.queue.Queue'].return_value)
        self.assertEqual(a.heartbeat_thread.thread_function, a._heartbeat)
        self.assertEqual(a.queue_thread.thread_function, a._process_queue)

    def test_register(self):
        a = Aggregator()

        objects = [
            ("dummy", "testkey", { "test_param" : "test_value", "test_param1": "test_value1" }),
            ("node", "testnode", { "test_param" : "test_value", "test_param1": "test_value1" })
            ]

        for o in objects:
            a.register(o[0], o[1], **o[2])
            a._reg_queue.put.assert_called_with({"method": "POST", "namespace": "resource", "res_type": o[0], "key": o[1]})
            send_obj = { "type" : o[0], "data" : { k : v for (k,v) in o[2].iteritems() } }
            if 'id' not in send_obj['data']:
                send_obj['data']['id'] = o[1]
            if o[0] == "node":
                self.assertEqual(a._registered["node"], send_obj)
            else:
                self.assertEqual(a._registered["entities"]["resource"][o[0]][o[1]], send_obj)

    def test_unregister(self):
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
        self.mocks['gevent.spawn'].side_effect = lambda f : mock.MagicMock(thread_function=f)
        a = Aggregator()

        self.assertTrue(a._running)

        a.stop()

        self.assertFalse(a._running)
        a.heartbeat_thread.join.assert_called_with()
        a.queue_thread.join.assert_called_with()

    def test_heartbeat_registers(self):
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

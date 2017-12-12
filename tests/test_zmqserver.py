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
import zmq
from nmoscommon.zmqserver import *

class NormalTestExit(Exception):
    pass

class TestZmqServer(unittest.TestCase):

    @mock.patch("nmoscommon.zmqserver.ServerWorker")
    @mock.patch("zmq.proxy")
    @mock.patch("zmq.Context")
    def test_run(self, Context, proxy, ServerWorker):
        callback = mock.MagicMock(name="callback")
        numWorkers = 5
        host = "dummyhost"
        port = 12345

        sockets = {}
        def socket(t):
            if t not in sockets:
                sockets[t] = []
            sockets[t].append(mock.MagicMock(name="socket_of_type_" + str(t)))
            return sockets[t][-1]
        Context.return_value.socket.side_effect = socket

        workers = [ mock.MagicMock(name="Worker" + str(n)) for n in range(0,numWorkers) ]
        ServerWorker.side_effect = [ x for x in workers ]

        UUT = ZmqServer(callback, numWorkers=numWorkers, host=host, port=port)

        UUT.run()

        self.assertIn(zmq.ROUTER, sockets)
        self.assertEqual(len(sockets[zmq.ROUTER]), 1)
        sockets[zmq.ROUTER][0].bind.assert_called_once_with('tcp://' + host + ":" + str(port))

        self.assertIn(zmq.DEALER, sockets)
        self.assertEqual(len(sockets[zmq.DEALER]), 1)
        sockets[zmq.DEALER][0].bind.assert_called_once_with('inproc://backend')

        self.assertListEqual(ServerWorker.mock_calls, [ mock.call(callback, Context.return_value) for _ in range(0, numWorkers) ])
        for w in workers:
            w.start.assert_called_once_with()

        proxy.assert_called_once_with(sockets[zmq.ROUTER][0], sockets[zmq.DEALER][0])

    @mock.patch("nmoscommon.zmqserver.ServerWorker")
    @mock.patch("zmq.proxy")
    @mock.patch("zmq.Context")
    def test_run__handles_exception_in_proxy(self, Context, proxy, ServerWorker):
        callback = mock.MagicMock(name="callback")
        numWorkers = 5
        host = "dummyhost"
        port = 12345

        proxy.side_effect = zmq.ZMQError

        sockets = {}
        def socket(t):
            if t not in sockets:
                sockets[t] = []
            sockets[t].append(mock.MagicMock(name="socket_of_type_" + str(t)))
            return sockets[t][-1]
        Context.return_value.socket.side_effect = socket

        workers = [ mock.MagicMock(name="Worker" + str(n)) for n in range(0,numWorkers) ]
        ServerWorker.side_effect = [ x for x in workers ]

        UUT = ZmqServer(callback, numWorkers=numWorkers, host=host, port=port)

        UUT.run()

        self.assertIn(zmq.ROUTER, sockets)
        self.assertEqual(len(sockets[zmq.ROUTER]), 1)
        sockets[zmq.ROUTER][0].bind.assert_called_once_with('tcp://' + host + ":" + str(port))

        self.assertIn(zmq.DEALER, sockets)
        self.assertEqual(len(sockets[zmq.DEALER]), 1)
        sockets[zmq.DEALER][0].bind.assert_called_once_with('inproc://backend')

        self.assertListEqual(ServerWorker.mock_calls, [ mock.call(callback, Context.return_value) for _ in range(0, numWorkers) ])
        for w in workers:
            w.start.assert_called_once_with()

        proxy.assert_called_once_with(sockets[zmq.ROUTER][0], sockets[zmq.DEALER][0])

    @mock.patch("nmoscommon.zmqserver.ServerWorker")
    @mock.patch("zmq.proxy")
    @mock.patch("zmq.Context")
    def test_stop(self, Context, proxy, ServerWorker):
        callback = mock.MagicMock(name="callback")
        numWorkers = 5
        host = "dummyhost"
        port = 12345

        sockets = {}
        def socket(t):
            if t not in sockets:
                sockets[t] = []
            sockets[t].append(mock.MagicMock(name="socket_of_type_" + str(t)))
            return sockets[t][-1]
        Context.return_value.socket.side_effect = socket

        workers = [ mock.MagicMock(name="Worker" + str(n)) for n in range(0,numWorkers) ]
        ServerWorker.side_effect = [ x for x in workers ]

        UUT = ZmqServer(callback, numWorkers=numWorkers, host=host, port=port)

        UUT.run()

        self.assertIn(zmq.ROUTER, sockets)
        self.assertEqual(len(sockets[zmq.ROUTER]), 1)
        sockets[zmq.ROUTER][0].bind.assert_called_once_with('tcp://' + host + ":" + str(port))

        self.assertIn(zmq.DEALER, sockets)
        self.assertEqual(len(sockets[zmq.DEALER]), 1)
        sockets[zmq.DEALER][0].bind.assert_called_once_with('inproc://backend')

        self.assertListEqual(ServerWorker.mock_calls, [ mock.call(callback, Context.return_value) for _ in range(0, numWorkers) ])
        for w in workers:
            w.start.assert_called_once_with()

        proxy.assert_called_once_with(sockets[zmq.ROUTER][0], sockets[zmq.DEALER][0])

        for w in workers:
            w.is_finished.return_value = False
            def set_finished_after_delay(obj, n):
                def __inner():
                    obj.is_finished.side_effect = [ False for _ in range(0,n) ] + [ True ]
                return __inner
            w.stop.side_effect = set_finished_after_delay(w,2)

        UUT.stop()

        for w in workers:
            w.stop.assert_called_once_with()

        Context.return_value.destroy.assert_called_once_with()


class TestServerWorker(unittest.TestCase):

    @mock.patch("zmq.Poller")
    def test_run(self, Poller):
        callback = mock.MagicMock(name="callback", side_effect=lambda msg : { "callback_param" : msg })
        context = mock.MagicMock(name="context")

        poll_responses = [ [ (context.socket.return_value, mock.sentinel.DUMMY0), (mock.sentinel.DUMMY1, mock.sentinel.DUMMY2), ],
                               [ (context.socket.return_value, mock.sentinel.DUMMY3), ] ]
        good_data = { "foo" : "bar", "baz" : ["boop",] }
        bad_data  = "}"
        context.socket.return_value.recv_multipart.side_effect = [ (mock.sentinel.ident0, json.dumps(good_data)), (mock.sentinel.ident1, bad_data), Exception  ]

        UUT = ServerWorker(callback, context)

        def poll_side_effect(*args, **kwargs):
            if len(poll_responses) > 0:
                return poll_responses.pop(0)
            else:
                UUT.stop()
                return []
        Poller.return_value.poll.side_effect = poll_side_effect

        self.assertTrue(UUT.amRunning)
        self.assertFalse(UUT.finished)

        UUT.run()

        context.socket.assert_called_once_with(zmq.DEALER)
        Poller.return_value.register.assert_called_once_with(context.socket.return_value, zmq.POLLIN)
        context.socket.return_value.connect.assert_called_once_with('inproc://backend')

        self.assertListEqual(context.socket.return_value.send_multipart.mock_calls,
                                 [ mock.call([mock.sentinel.ident0, json.dumps({ "callback_param" : good_data })]),
                                       mock.call([mock.sentinel.ident1, json.dumps([400])]) ])
        self.assertTrue(UUT.is_finished())

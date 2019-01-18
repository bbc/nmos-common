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
import json
from nmoscommon.webSocketClient import *


class NormalTestExit(Exception):
    pass

class TestWebSocketClient(unittest.TestCase):

    @mock.patch("websocket.WebSocketApp")
    def test_run(self, WebSocketApp):
        # Make this raise an exception so that the run loop will exit once we've tested what we want to test
        WebSocketApp.return_value.run_forever.side_effect = NormalTestExit

        UUT = WebSocketClient(mock.sentinel.wsAddr)

        self.assertFalse(UUT.started.is_set())

        with self.assertRaises(NormalTestExit):
            UUT.run()

        WebSocketApp.assert_called_once_with(mock.sentinel.wsAddr,
                                         on_message=mock.ANY,
                                         on_error=mock.ANY,
                                         on_close=mock.ANY,
                                         on_open=mock.ANY)
        WebSocketApp.return_value.run_forever.assert_called_once_with(sslopt=None)
        self.assertTrue(UUT.started.is_set())

    @mock.patch("websocket.WebSocketApp")
    def test_run_keeps_going_if_run_forever_exits(self, WebSocketApp):
        # Make this raise an exception so that the run loop will exit once we've tested what we want to test
        WebSocketApp.return_value.run_forever.side_effect = [ None, NormalTestExit ]

        UUT = WebSocketClient(mock.sentinel.wsAddr)

        self.assertFalse(UUT.started.is_set())

        with self.assertRaises(NormalTestExit):
            UUT.run()

        WebSocketApp.assert_called_once_with(mock.sentinel.wsAddr,
                                         on_message=mock.ANY,
                                         on_error=mock.ANY,
                                         on_close=mock.ANY,
                                         on_open=mock.ANY)
        self.assertListEqual(WebSocketApp.return_value.run_forever.mock_calls,
                                 [ mock.call(sslopt=None), mock.call(sslopt=None) ] )
        self.assertTrue(UUT.started.is_set())

    @mock.patch("websocket.WebSocketApp")
    def test_run_will_exit_if_close_is_called_and_serve_forever_exits(self, WebSocketApp):
        # Make this raise an exception so that the run loop will exit once we've tested what we want to test
        UUT = WebSocketClient(mock.sentinel.wsAddr)

        WebSocketApp.return_value.run_forever.side_effect = lambda sslopt: UUT.stop()
        self.assertFalse(UUT.started.is_set())

        UUT.run()

        WebSocketApp.assert_called_once_with(mock.sentinel.wsAddr,
                                         on_message=mock.ANY,
                                         on_error=mock.ANY,
                                         on_close=mock.ANY,
                                         on_open=mock.ANY)
        self.assertListEqual(WebSocketApp.return_value.run_forever.mock_calls,
                                 [ mock.call(sslopt=None) ] )
        self.assertTrue(UUT.started.is_set())

    @mock.patch("websocket.WebSocketApp")
    def test_callbacks(self, WebSocketApp):
        # Make this raise an exception so that the run loop will exit once we've tested what we want to test
        WebSocketApp.return_value.run_forever.side_effect = NormalTestExit
        UUT = WebSocketClient(mock.sentinel.wsAddr)
        with mock.patch.object(UUT, 'onMessage') as onMessage:
            with mock.patch.object(UUT, 'onError') as onError:
                with mock.patch.object(UUT, 'onClose') as onClose:
                    with mock.patch.object(UUT, 'onOpen') as onOpen:
                        with self.assertRaises(NormalTestExit):
                            UUT.run()
                        WebSocketApp.assert_called_once_with(mock.sentinel.wsAddr,
                                                                 on_message=mock.ANY,
                                                                 on_error=mock.ANY,
                                                                 on_close=mock.ANY,
                                                                 on_open=mock.ANY)

                        onOpen.assert_not_called()
                        WebSocketApp.call_args[1]['on_open'](mock.sentinel.ws)
                        onOpen.assert_called_once_with()

                        onMessage.assert_not_called()
                        WebSocketApp.call_args[1]['on_message'](mock.sentinel.ws, mock.sentinel.msg)
                        onMessage.assert_called_once_with(mock.sentinel.msg)

                        onError.assert_not_called()
                        WebSocketApp.call_args[1]['on_error'](mock.sentinel.ws, mock.sentinel.error)
                        onError.assert_called_once_with(mock.sentinel.error)

                        onClose.assert_not_called()
                        WebSocketApp.call_args[1]['on_close'](mock.sentinel.ws)
                        onClose.assert_called_once_with()

    @mock.patch("websocket.WebSocketApp")
    def test_sendJSON(self, WebSocketApp):
        ws = mock.MagicMock(name="ws")
        WebSocketApp.return_value.run_forever.side_effect = NormalTestExit
        UUT = WebSocketClient(mock.sentinel.wsAddr)
        with self.assertRaises(NormalTestExit):
            UUT.run()
        WebSocketApp.call_args[1]['on_open'](ws)
        msg = { "foo" : "bar", "baz" : [ "boop" ] }

        UUT.sendJSON(msg)
        ws.send.assert_called_once_with(json.dumps(msg))

    @mock.patch("websocket.WebSocketApp")
    def test_sendPlain(self, WebSocketApp):
        ws = mock.MagicMock(name="ws")
        WebSocketApp.return_value.run_forever.side_effect = NormalTestExit
        UUT = WebSocketClient(mock.sentinel.wsAddr)
        with self.assertRaises(NormalTestExit):
            UUT.run()
        WebSocketApp.call_args[1]['on_open'](ws)
        msg = "laskjchd; wfh[j"

        UUT.sendPlain(msg)
        ws.send.assert_called_once_with(msg)


    @mock.patch("websocket.WebSocketApp")
    def test_defaultCallbacks(self, WebSocketApp):
        ws = mock.MagicMock(name="ws")
        WebSocketApp.return_value.run_forever.side_effect = NormalTestExit
        UUT = WebSocketClient(mock.sentinel.wsAddr)
        with self.assertRaises(NormalTestExit):
            UUT.run()
        WebSocketApp.call_args[1]['on_open'](ws)
        WebSocketApp.call_args[1]['on_message'](mock.sentinel.ws, mock.sentinel.msg)
        with self.assertRaises(Exception):
            WebSocketApp.call_args[1]['on_error'](mock.sentinel.ws, mock.sentinel.error)
        WebSocketApp.call_args[1]['on_close'](ws)

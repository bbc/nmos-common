import unittest
import uuid
import json
import time
import gevent
from ipppython.webSocketClient import WebSocketClient
from ipppython.webapi import WebAPI, route, on_json
from ipppython.httpserver import HttpServer
from functools import wraps
from socket import error as socket_error

# Time in seconds to wait for messages to arrive
TIMEOUT = 1


class mockWebSocketServer(WebAPI):

    def __init__(self):
        # over-ride default websocket handler
        self.on_websocket_connect = self.websocket_opened
        self.subscribers = {}
        self.newMessage = False
        self.receievedMessage = ""
        super(mockWebSocketServer, self).__init__()

    def sendMessage(self, message):
        for wsid, ws in self.subscribers.iteritems():
            ws.send(json.dumps(message))

    @route("/")
    def serverRoot(self):
        return ['ws/']

    @on_json('/ws/')
    def __ws(self, ws, message):
        self.newMessage = True
        self.receievedMessage = message
        return

    def websocket_opened(self, handler_func):
        @wraps(handler_func)
        def inner_func(ws):
            # Called each time a new websocket is created.
            # Over-rides the default Webapi websocket hander
            print("New websocket established")
            websocketId = str(uuid.uuid4())
            self.subscribers[websocketId] = ws
            while True:
                # We're in our own gevent thread - just keep
                # listening out for any messages on the socket
                try:
                    # Blocking
                    message = ws.receive()
                except socket_error:
                    message = None
                except Exception as ex:
                    message = None

                if message is not None:
                    # call the 'on_json' route to deal with the messsage
                    handler_func(ws, message)
                else:
                    # gevent-websockets states that None
                    # from receive() means "closed or errored"
                    self.subscribers.pop(websocketId)
                    print("Websocket closed")
                    break
        return inner_func


class myClient(WebSocketClient):

    def __init__(self, wsAddr):
        super(myClient, self).__init__(wsAddr)
        self.newMessage = False
        self.opened = False
        self.closed = False
        self.latestMessage = ""

    def onMessage(self, message):
        self.latestMessage = json.loads(message)
        self.newMessage = True

    def onClose(self):
        self.closed = True

    def onOpen(self):
        self.opened = True


class testWebsocketClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.httpServer = HttpServer(
            mockWebSocketServer,
            port=8090
        )
        cls.httpServer.start()
        while not cls.httpServer.started.is_set():
            cls.httpServer.started.wait()
        cls.websocketServer = cls.httpServer.api
        cls.dut = myClient("ws://localhost:8090/ws/")
        cls.dut.start()
        while not cls.dut.started.is_set():
            cls.dut.started.wait()
        while not cls.dut.opened:
            pass

    def test_receive_message(self):
        """Check that messages can go from the server
        to the client"""
        expected = {"test": "test"}
        self.websocketServer.sendMessage(expected)
        startTime = time.time()
        while not self.dut.newMessage:
            # Wait for the message to arrive at the client
            # up to the time set by TIMEOUT
            if time.time() - startTime > TIMEOUT:
                raise Exception("Test failed due to timeout")
                break
        actual = self.dut.latestMessage
        self.assertEqual(expected, actual)

    def test_send_json(self):
        expected = {"test": "test"}
        self.dut.sendJSON(expected)
        startTime = time.time()
        while not self.websocketServer.newMessage:
            if time.time() - startTime > TIMEOUT:
                raise Exception("Test failed due to timeout")
                break
        actual = self.websocketServer.receievedMessage
        self.assertEqual(expected, actual)

    @classmethod
    def tearDownClass(cls):
        cls.dut.stop()
        # Bodge to ensure the client fully shuts down
        # before the server or it will moan
        gevent.sleep(1)
        cls.httpServer.stop()


if __name__ == "__main__":
    # run up websocket test server without tests
    httpServer = HttpServer(
        mockWebSocketServer,
        port=8090
    )
    httpServer.start()
    while not httpServer.started.is_set():
        print 'Waiting for HTTP server to start...'
        httpServer.started.wait()
    httpServer.join()

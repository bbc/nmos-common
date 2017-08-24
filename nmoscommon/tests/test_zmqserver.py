#! /usr/bin/python

import unittest
import zmq
import sys
from nmoscommon.zmqserver import ZmqServer
import threading
import json


class TestZmqServer(unittest.TestCase):

    def setUp(self):
        self.server = ZmqServer(self._serverCallback)
        self.callbackReceived = {}
        self.callbackData = {}
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def _callback(self, data, ident):
        self.callbackReceived[ident] = True
        self.callbackData[ident] = data

    def _serverCallback(self, data):
        return data

    def test_server(self):
        clients = []
        for i in range(2):
            client = ClientT(i, self._callback)
            client.start()
            client.sendMessage({"action": "testJSON"})
            clients.append(client)
            self.callbackReceived[i] = False

        for i in range(2):
            while not self.callbackReceived[i]:
                pass
            self.assertEqual(json.loads(self.callbackData[i]),
                             {"action": "testJSON"})
            clients[i].amRunning = False

def tprint(msg):
    """like print, but won't get newlines confused with multiple threads"""
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()


class ClientT(threading.Thread):
    """ClientTask"""
    def __init__(self, id, callback):
        self.id = id
        self.amRunning = True
        self.messages = []
        self.callback = callback
        threading.Thread.__init__(self)

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        identity = u'worker-%d' % self.id
        socket.identity = identity.encode('ascii')
        socket.connect('tcp://localhost:5570')
        poll = zmq.Poller()
        poll.register(socket, zmq.POLLIN)
        while self.amRunning:
            while len(self.messages) > 0:
                message = self.messages.pop()
                socket.send_json(message)
            sockets = dict(poll.poll(1000))
            if socket in sockets:
                msg = socket.recv()
                self.callback(msg, self.id)

        socket.close()
        context.term()

    def sendMessage(self, message):
        self.messages.append(message)

if __name__ == '__main__':
    unittest.main()

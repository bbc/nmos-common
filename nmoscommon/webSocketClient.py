import websocket
import signal
import sys
import threading
import json

# This is a very thin wrapper around python WebSocketApp
# to allow easy use with threading by inheriting threading.Thread


class WebSocketClient(threading.Thread):
    daemon = True

    def __init__(self, wsAddr, sslopt=None):
        self.started = threading.Event()
        self.wsAddr = wsAddr
        self._keep_running = False
        threading.Thread.__init__(self)
        self.sslopt = sslopt

    def run(self):
        self._keep_running = True
        self.ws = websocket.WebSocketApp(self.wsAddr,
                                         on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close,
                                         on_open=self._on_open)
        while self._keep_running:
            self.__setstarted()
            self.ws.run_forever(sslopt=self.sslopt)

    def __setstarted(self):
        self.started.set()

    # These are just here to make the function signatures work
    # the user shouldn't be fiddling with the ws

    def _on_message(self, ws, message):
        self.onMessage(message)

    def _on_error(self, ws, error):
        self.onError(error)

    def _on_close(self, ws):
        self.onClose()

    def _on_open(self, ws):
        # Grab the websocket so we can use it to send later
        self.ws = ws
        self.onOpen()

    def onMessage(self, message):
        # over-ride this method in child class
        # to alter message handling behaviour
        pass

    def onError(self, error):
        # over-ride this method in child class
        # to alter error handling behaviour
        raise Exception(error)

    def onClose(self):
        # over-ride this method in child class
        # to alter actions when the websocket
        # is closed
        pass

    def onOpen(self):
        # over-ride this method in child class
        # to alter startup behaviour
        pass

    def sendJSON(self, message):
        self.ws.send(json.dumps(message))

    def sendPlain(self, message):
        self.ws.send(message)

    def stop(self):
        self._keep_running = False
        self.ws.close()


if __name__ == "__main__":  # pragma: no cover
    websocketClient = WebSocketClient("ws://localhost:8090/ws/")

    def signal_handler(rxsignal, frame):
        websocketClient.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    websocketClient.run()

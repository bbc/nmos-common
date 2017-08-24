from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
import threading
from flask import request
import socket

class HttpServer(threading.Thread):
  daemon = True    # causes server to stop on main thread quitting
  def __init__(self, api, port=0, host='0.0.0.0', api_args=None, api_kwargs=None, ssl=None):
    self.api_args = api_args
    self.api_kwargs = api_kwargs
    if self.api_args is None:
      self.api_args = []
    if self.api_kwargs is None:
      self.api_kwargs = {}
    self.api_class = api
    self.port = port
    self.host = host
    self.started = threading.Event()
    self.failed = None
    self.ssl = ssl

    threading.Thread.__init__(self)

  def run(self):
    self.api = self.api_class(*self.api_args, **self.api_kwargs)

    port = self.port

    while True:
      if self.port == 0:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 0))
        self.port = sock.getsockname()[1]
        sock.close()

      if self.port == 0:
        print "ERROR! Port still 0!"
        break

      try:
        #        self.api.app.before_first_request = self.__setstarted()

        if self.ssl is not None:
            self.server = WSGIServer((self.host,self.port), self.api.app, handler_class=WebSocketHandler, **self.ssl)
        else:
            self.server = WSGIServer((self.host,self.port), self.api.app, handler_class=WebSocketHandler)

        self.server.start()
        self.__setstarted()
        self.server.serve_forever()
      except socket.error as e:
        if e.errno == 48:
          if port != 0:
            raise
          else:
            self.port = port
            continue
        else:
          self.failed = e
          self.__setstarted()
      break

  def stop(self):
    self.api.stop()

  def __setstarted(self):
    self.api.port = self.port
    self.started.set()
    if self.failed is None:
      print "HttpServer running"
    else:
      print "HttpServer failed to start"

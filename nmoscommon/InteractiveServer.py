import sys
import SocketServer
from code import InteractiveConsole

interpreter_globals = {}

class InteractiveServer(SocketServer.BaseRequestHandler):
    def handle(self):
        global interpreter_globals

        file = self.request.makefile()
        shell = Shell(file, locals=interpreter_globals)
        try:
            shell.interact()
        except SystemExit:
            pass


class Shell(InteractiveConsole):
    def __init__(self, file, *args, **kwargs):
        self.file = sys.stdout = file
        InteractiveConsole.__init__(self, *args, **kwargs)
        return

    def write(self, data):
        self.file.write(data)
        self.file.flush()

    def raw_input(self, prompt=""):
        self.write(prompt)
        return self.file.readline()

def interact(address=("0.0.0.0",9999)):
    server = SocketServer.TCPServer(address, InteractiveServer)
    server.serve_forever()

port = 9999
if __name__ == '__main__':
    import threading
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    interact(("0.0.0.0",port))

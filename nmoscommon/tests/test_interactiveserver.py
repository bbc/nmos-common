import unittest
import mock
import nmoscommon
from nmoscommon.InteractiveServer import interact, InteractiveServer, interpreter_globals, Shell
import code
import sys
import runpy

class TestInteractiveServer(unittest.TestCase):
    @mock.patch('SocketServer.TCPServer')
    def test_interact(self, tcpserver):
        interact()
        tcpserver.assert_called_with(("0.0.0.0",9999), InteractiveServer)
        tcpserver.return_value.serve_forever.assert_called_with()

    @mock.patch.object(code.InteractiveConsole, 'interact')
    def test_InteractiveServer(self, ic_interact):
        stdout = sys.stdout
        server = InteractiveServer(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        sys.stdout = stdout
        ic_interact.assert_called_with()

    @mock.patch.object(code.InteractiveConsole, 'interact')
    def test_InteractiveServer_exits_cleanly(self, ic_interact):
        ic_interact.side_effect = SystemExit
        stdout = sys.stdout
        try:
            server = InteractiveServer(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        except:
            sys.stdout = stdout
            self.fail("InteractiveServer raised an unexpected exception")
        sys.stdout = stdout
        ic_interact.assert_called_with()

    def test_Shell_write(self):
        stdout = sys.stdout
        f = mock.MagicMock()
        shell = Shell(f)
        sys.stdout = stdout

        data = "THIS IS SOME DUMMY DATA"

        shell.write(data)
        f.write.assert_called_with(data)
        f.flush.assert_called_with()

    def test_Shell_raw_input(self):
        stdout = sys.stdout
        f = mock.MagicMock()
        shell = Shell(f)
        sys.stdout = stdout

        data = "THIS IS SOME DUMMY DATA"

        rval = shell.raw_input(prompt=data)
        f.write.assert_called_with(data)
        f.flush.assert_called_with()
        f.readline.assert_called_with()
        self.assertEqual(rval, f.readline.return_value)

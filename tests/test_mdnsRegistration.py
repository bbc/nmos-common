import unittest
from nmoscommon.mdns.mdnsRegistration import MDNSRegistration
from mock import MagicMock, patch


class TestMDNSEngine(unittest.TestCase):

    def setUp(self):
        self.zeroconf = MagicMock()
        self.name = "testName"
        self.regType = "_nmos-test_tcp"
        self.port = 8080,
        self.txtRecord = {}
        self.dut = self.build_dut()

    def build_dut(self):
        return MDNSRegistration(
            self.zeroconf,
            self.name,
            self.regType,
            self.port,
            self.txtRecord
        )

    def test_registration(self):
        with patch('nmoscommon.mdns.mdnsRegistration.ServiceInfo') as info:
            self.dut = self.build_dut()
            regFunc = self.dut.zeroconf.register_service = MagicMock()
            self.dut.register()
            self.assertTrue(regFunc.called)
            argv, kwargs = info.call_args
        expected = {
            "type": self.regType + '.local.',
            "name": self.name,
            "port": self.port,
            "properties": self.txtRecord
        }
        self.assertDictEqual(expected, kwargs)

    def test_unregister(self):
        unregFunc = self.dut.zeroconf.unregister_service = MagicMock()
        self.dut.unRegister()
        self.assertTrue(unregFunc.called)

import unittest
from socket import inet_aton
from mock import MagicMock, patch
from nmoscommon.mdns import MDNSEngine

class TestDNSListener(unittest.TestCase):

    def setUp(self, *args, **kwargs):
        self.callbackMethod = MagicMock()
        self.dut = MDNSEngine()
        self.zeroconf = MagicMock()
        self.dut.zeroconf = self.zeroconf
        self.dut.start()

        self.mockValues = {
            "addr": "192.168.0.1",
            "addrBin": inet_aton("192.168.0.1"),
            "name": "serviceName",
            "regType": "_nmos-test._tcp",
            "port": 12345
        }

    def test_stop(self):
        stop = MagicMock()
        self.dut.zeroconf.close = stop
        self.dut.stop()
        stop.assert_called()

    def test_using_correct_regtype(self):
        callback = MagicMock()
        with patch('nmoscommon.mdns.mdnsSubscription.ServiceBrowser') as subscription:
            self.dut.callback_on_services(self.mockValues["regType"], callback)
            actualRegtype = subscription.call_args[0][1]
            self.assertEqual(self.mockValues["regType"] + ".local.", actualRegtype)

    def test_callback_on_services_add(self):
        callback = self.call_service_change("add")
        self.check_callback_okay(callback, "add")

    def test_callback_on_services_remove(self):
        callback = self.call_service_change("remove")
        self.check_callback_okay(callback, "remove")

    def test_register_only(self):
        callback = self.call_service_change("remove", True)
        callback.assert_not_called()

    def call_service_change(self, action, registerOnly=False):
        callback = MagicMock()
        zeroconf = self.build_mock_zeroconf()
        with patch('nmoscommon.mdns.mdnsSubscription.ServiceBrowser') as subscription:
            self.dut.callback_on_services(self.mockValues["regType"], callback, registerOnly=registerOnly)
            actualListener = subscription.call_args[0][2]
            if action == "add":
                method = actualListener.add_service
            else:
                method = actualListener.remove_service
            method(
                zeroconf,
                self.mockValues["regType"],
                self.mockValues["name"]
            )
        return callback

    def check_callback_okay(self, callback, action):
        callback.assert_called()
        response = callback.call_args[0][0]
        self.check_callback_response(response, action)

    def check_callback_response(self, response, action):
        self.assertEqual(response['action'], action)
        self.assertEqual(response['ip'], self.mockValues['addr'])
        self.assertEqual(response['type'], self.mockValues['regType'])
        self.assertEqual(response['name'], self.mockValues['name'])
        self.assertEqual(response['port'], self.mockValues['port'])

    def build_mock_zeroconf(self):
        zeroConf = MagicMock()
        zeroConf.getServiceInfo = MagicMock()
        info = MagicMock()
        info.type = self.mockValues["regType"]
        info.name = self.mockValues["name"]
        info.port = self.mockValues["port"]
        info.address = self.mockValues["addrBin"]
        zeroConf.get_service_info.return_value = info
        return zeroConf

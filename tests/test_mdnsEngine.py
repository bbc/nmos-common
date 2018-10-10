import unittest
from socket import inet_aton
from mock import MagicMock, patch
from nmoscommon.mdns import MDNSEngine


class TestDNSListener(unittest.TestCase):

    def setUp(self):
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

    """Check that stopping the Class stops zeroconf"""
    def test_stop(self):
        stop = MagicMock()
        self.dut.zeroconf.close = stop
        self.dut.stop()
        self.assertTrue(stop.called)

    """Check that .local. is appended to the reg type"""
    def test_using_correct_regtype(self):
        callback = MagicMock()
        with patch('nmoscommon.mdns.mdnsSubscription.ServiceBrowser') as subscription:
            self.dut.callback_on_services(self.mockValues["regType"], callback)
            actualRegtype = subscription.call_args[0][1]
            self.assertEqual(self.mockValues["regType"] + ".local.", actualRegtype)

    """Check that the add callback is called when an mDNSservice is added"""
    def test_callback_on_services_add(self):
        callback = self.call_service_change("add")
        self.check_callback_okay(callback, "add")

    """Check that the remove callback is called when an mDNS service is removed"""
    def test_callback_on_services_remove(self):
        callback = self.call_service_change("remove")
        self.check_callback_okay(callback, "remove")

    """Check that the remove callback isn't used when register only is true"""
    def test_register_only(self):
        callback = self.call_service_change("remove", True)
        callback.assert_not_called()

    """Helper mehtod, tests various mDSN callback permutations"""
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

    """Helper method, checks that callbacks alerting to mDNS changes are made correctly"""
    def check_callback_okay(self, callback, action):
        self.assertTrue(callback.called)
        response = callback.call_args[0][0]
        self.check_callback_response(response, action)

    """Helper method, checks the contents of mDNS callbacks"""
    def check_callback_response(self, response, action):
        self.assertEqual(response['action'], action)
        self.assertEqual(response['ip'], self.mockValues['addr'])
        self.assertEqual(response['type'], self.mockValues['regType'])
        self.assertEqual(response['name'], self.mockValues['name'])
        self.assertEqual(response['port'], self.mockValues['port'])

    """Helper method, builds a pretend zeroconf instance to get a service's information from"""
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

    """Test all subscriptions are closed"""
    def test_close_all_subscriptions(self):
        mocks = []
        for i in range(0, 5):
            mocks.append(MagicMock())
            self.dut.subscriptions.append(MagicMock())
            self.dut.subscriptions[i].close = mocks[i]
        self.dut._close_all_subscriptions()
        for i in range(0, 5):
            self.assertTrue(mocks[i].called)
        self.assertEqual(self.dut.subscriptions, [])

    """Check that all mDNS services can be closed"""
    def test_close_all_services(self):
        self.dut.zeroconf = MagicMock()
        mock = MagicMock()
        unreg = mock.unRegister = MagicMock()
        testStructure = {
            "type1": {
                "name1": mock,
                "name2": mock
            },
            "type2": {
                "name1": mock,
                "name2": mock,
            },
            "type3": {
                "name1": mock
            }
        }
        self.dut.advertisedServices = testStructure
        self.dut._close_all_services()
        self.assertEqual(unreg.call_count, 5)
        self.assertEqual(self.dut.advertisedServices, {})

    """Test adding an advertised service when none are already advertised"""
    def test_add_info_to_advertised_services_empty(self):
        mockReg = MagicMock()
        mockReg.name = "name"
        mockReg.regtype = "type"
        self.dut.advertisedServices = {}
        self.dut._add_registration_to_advertised_services(mockReg)
        self.assertEqual({"type": {"name": mockReg}}, self.dut.advertisedServices)

    """Test adding an advertised service when there is a different type already present"""
    def test_add_info_to_advertised_services_existing_type(self):
        mockReg = MagicMock()
        mockReg.name = "name2"
        mockReg.regtype = "type2"
        self.dut.advertisedServices = {
            "type": {
                "name": "info"
            }
        }
        self.dut._add_registration_to_advertised_services(mockReg)
        self.assertDictEqual({
            "type": {
                "name": "info"
            },
            "type2": {
                "name2": mockReg
            }
        }, self.dut.advertisedServices)

    """Test adding an advertised service when there is a name entry already in the same type"""
    def test_add_info_to_advertised_services_existing_name(self):
        mockReg = MagicMock()
        mockReg.name = "name2"
        mockReg.regtype = "type"
        self.dut.advertisedServices = {
            "type": {
                "name": "info"
            }
        }
        self.dut._add_registration_to_advertised_services(mockReg)
        self.assertDictEqual({
            "type": {
                "name": "info",
                "name2": mockReg
            }
        }, self.dut.advertisedServices)

    """Test removing an mDNS service from the advertised services"""
    def test_remove_registration_from_advertised_services(self):
        self.dut.advertisedServices = {"type": {"name": "info"}}
        self.dut._remove_registration_from_advertised_services("type", "name")
        self.assertEqual(self.dut.advertisedServices, {})

        self.dut.advertisedServices = {"type": {"name": "info", "name2": "info2"}}
        self.dut._remove_registration_from_advertised_services("type", "name")
        self.assertDictEqual(self.dut.advertisedServices, {"type": {"name2": "info2"}})

#!/usr/bin/env python

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
from nmoscommon.mdns.mdnsInterfaceController import MDNSInterfaceController
from nmoscommon.mdns.mdnsExceptions import NoNetworkInterfacesFoundException
from mock import MagicMock, patch


class TestMDNSInterfaceController(unittest.TestCase):

    def setUp(self):
        self.logger = MagicMock()
        self.dut = MDNSInterfaceController(self.logger)

    """Check logic in default interface selection on file based return"""
    def test_get_default_interfaces_file(self):
        self.helper_prepare_interface_finders(["192.168.0.5"])
        self.helper_test_default_interface_logic()

    def test_get_default_interface_routing(self):
        self.helper_prepare_interface_finders(False, ["192.168.0.5"])
        self.helper_test_default_interface_logic()

    def test_get_default_interface_gateway(self):
        self.helper_prepare_interface_finders(False, False, ["192.168.0.5"])
        self.helper_test_default_interface_logic()

    def test_get_default_interface_none(self):
        self.helper_prepare_interface_finders(False, False, False)
        with self.assertRaises(NoNetworkInterfacesFoundException):
            self.helper_test_default_interface_logic()

    def test_get_default_interface_all(self):
        self.helper_prepare_interface_finders(False, False, False, ["192.168.0.5"])
        self.helper_test_default_interface_logic()

    def helper_test_default_interface_logic(self):
        self.dut.defaultInterfaces = []
        self.dut._get_default_interfaces()
        actual = self.dut.defaultInterfaces
        expected = ["192.168.0.5"]
        self.assertEqual(actual, expected)

    def helper_prepare_interface_finders(self, file, routing=False, gateway=False, all=False):
        self.dut._get_default_interface_from_file = MagicMock()
        self.dut._get_default_interface_from_file.return_value = file
        self.dut._get_default_interface_from_gateway = MagicMock()
        self.dut._get_default_interface_from_gateway.return_value = gateway
        self.dut._get_default_interface_from_routing_rules = MagicMock()
        self.dut._get_default_interface_from_routing_rules.return_value = routing
        self.dut._get_all_interfaces = MagicMock()
        self.dut._get_all_interfaces.return_value = all

        def mockMethod(param):
            return param
        self.dut.addInterface = MagicMock()
        self.dut.addInterface.side_effect = mockMethod

    """Check the controller can fall back to getting all interfaces"""
    def test_get_default_all_interface(self):
        with patch('nmoscommon.mdns.mdnsInterfaceController.netifaces') as netifaces:
            netifaces.ifaddresses = self.helper_netiface_interface()
            netifaces.AF_INET = 2
            netifaces.interfaces.return_value = ["eno1", "ens4f0"]
            expected = ["192.168.0.5", "192.168.0.4"]
            actual = self.dut._get_all_interfaces()
            self.assertEqual(actual, expected)

    """Check the controller can use ipphostname to get the local ip"""
    def test_get_default_interface_from_routing_rule(self):
        with patch('nmoscommon.mdns.mdnsInterfaceController.ipphostname') as hostname:
            getFunc = hostname.getLocalIP = MagicMock()
            getFunc.return_value = "192.168.0.5"
            with patch('nmoscommon.mdns.mdnsInterfaceController.ippUtilsAvailable') as available:
                available = True  # noqa: F841
                expected = ["192.168.0.5"]
                actual = self.dut._get_default_interface_from_routing_rules()
                self.assertEqual(actual, expected)

    """Check the controller can use nmoscommonconfig to get the default interface"""
    def test_get_default_interface_from_file(self):
        with patch('nmoscommon.mdns.mdnsInterfaceController.netifaces') as netifaces:
            netifaces.ifaddresses = self.helper_netiface_interface()
            netifaces.AF_INET = 2
            with patch('nmoscommon.mdns.mdnsInterfaceController.nmoscommonconfig') as config:
                config.config = {"interfaces": ["eno1"]}
                expected = ["192.168.0.5"]
                actual = self.dut._get_default_interface_from_file()
                self.assertEqual(actual, expected)

    """Check the controller can automatically find the default interface using netifaces"""
    def test_get_default_interface_from_gateway(self):
        with patch('nmoscommon.mdns.mdnsInterfaceController.netifaces') as netifaces:
            netifaces.gateways = self.helper_netiface_gateways()
            netifaces.ifaddresses = self.helper_netiface_interface()
            netifaces.AF_INET = 2
            actual = self.dut._get_default_interface_from_gateway()
            expected = ["192.168.0.5"]
            self.assertEqual(actual, expected)

    def helper_netiface_gateways(self):
        gatewaysMethod = MagicMock()
        returnValue = {'default': {2: (u'192.168.0.2', u'eno1'), 10: (u'0:0:0:0:0:ffff:c0a8:1402', u'ens4f0')},
                       2: [(u'192.168.02', u'eno1', False), (u'192.168.10.4', u'ens4f0', False),
                       (u'192.168.0.2', u'eno1', True)],
                       10: [(u'0:0:0:0:0:ffff:c0a8:1402', u'ens4f0', True)]}
        gatewaysMethod.return_value = returnValue
        return gatewaysMethod

    def helper_netiface_interface(self):
        interfaceMethod = MagicMock()

        def mockMethod(interface):
            returnValueEno1 = {17: [{'broadcast': u'ff:ff:ff:ff:ff:ff',
                                     'addr': u'64:51:06:2a:d8:9a'}],
                               2: [{'broadcast': u'192.168.0.255',
                                    'netmask': u'255.255.255.0',
                                    'addr': u'192.168.0.5'}],
                               10: [{'netmask': u'ffff:ffff:ffff:ffff::/64',
                                     'addr': u'fe80::6651:6ff:fe2a:d89a%eno1'}]}
            returnValueEns4f0 = {17: [{'broadcast': u'ff:ff:ff:ff:ff:ff',
                                       'addr': u'64:51:06:2a:d8:9a'}],
                                 2: [{'broadcast': u'192.168.0.255',
                                      'netmask': u'255.255.255.0',
                                      'addr': u'192.168.0.4'}],
                                 10: [{'netmask': u'ffff:ffff:ffff:ffff::/64',
                                       'addr': u'fe80::6651:6ff:fe2a:d89a%eno1'}]}
            if interface == "eno1":
                return returnValueEno1
            elif interface == "ens4f0":
                return returnValueEns4f0
            else:
                raise Exception(interface)
        interfaceMethod.side_effect = mockMethod
        return interfaceMethod

    """Check that adding duplicate interfaces does not produce a duplicate listing"""
    def test_add_interface(self):
        with patch('nmoscommon.mdns.mdnsInterfaceController.MDNSInterface') as interface:
            self.dut.interfaces = {}
            ret = MagicMock()
            interface.return_value = ret
            self.dut.addInterface("192.168.0.5")
            self.assertEqual(self.dut.interfaces, {"192.168.0.5": ret})
            self.dut.addInterface("192.168.0.5")
            self.assertEqual(self.dut.interfaces, {"192.168.0.5": ret})

    """Check interfaces can be retrieved"""
    def test_get_interfaces(self):
        expected = self.dut.defaultInterfaces = ["default"]
        actual = self.dut.getInterfaces([])
        self.assertEqual(expected, actual)

        self.dut.addInterface = MagicMock(side_effect=range(0, 5))
        actual = self.dut.getInterfaces(["a", "b", "c", "d", "e"])
        self.assertEqual(actual, list(range(0, 5)))

    """Test the class shuts all its interfaces correctly"""
    def test_close(self):
        mockInterface = MagicMock()
        closeMethod = MagicMock()
        mockInterface.close = closeMethod
        testStructure = {
            "a": mockInterface,
            "b": mockInterface,
            "c": mockInterface
        }
        self.dut.interfaces = testStructure
        self.dut.close()
        self.assertEqual(closeMethod.call_count, 3)


if __name__ == "__main__":
    unittest.main()

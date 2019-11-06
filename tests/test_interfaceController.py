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
import netifaces
from mock import MagicMock, patch, sentinel

from nmoscommon.interfaceController import InterfaceController


class TestInterfaceController(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.dut = InterfaceController(self.logger)

    def test_get_default_interfaces_file(self):
        """Check logic in default interface selection on file based return"""
        self.helper_prepare_interface_finders(["192.168.0.5"])
        self.helper_test_default_interface_logic()

    def test_get_default_interface_routing(self):
        self.helper_prepare_interface_finders([], ["192.168.0.5"])
        self.helper_test_default_interface_logic()

    def test_get_default_interface_gateway(self):
        self.helper_prepare_interface_finders([], [], ["192.168.0.5"])
        self.helper_test_default_interface_logic()

    def test_get_default_interface_none(self):
        self.helper_prepare_interface_finders([], [], [])
        self.assertFalse(self.dut.get_default_interfaces())

    def test_get_default_interface_all(self):
        self.helper_prepare_interface_finders([], [], [], ["192.168.0.5"])
        self.helper_test_default_interface_logic()

    def helper_test_default_interface_logic(self):
        actual = self.dut.get_default_interfaces()
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

    @patch('nmoscommon.interfaceController.ipphostname')
    def test_get_default_interface_from_routing_rule(self, hostname):
        """Check the controller can use ipphostname to get the local ip"""
        getFunc = hostname.getLocalIP = MagicMock()
        getFunc.return_value = "192.168.0.5"
        with patch('nmoscommon.interfaceController.ippUtilsAvailable') as available:
            available = True  # noqa: F841
            expected = ["192.168.0.5"]
            actual = self.dut._get_default_interface_from_routing_rules()
            self.assertEqual(actual, expected)

    @patch('nmoscommon.interfaceController.netifaces')
    def test_get_default_interface_from_file(self, netifaces):
        """Check the controller can use nmoscommonconfig to get the default interface"""
        netifaces.ifaddresses = self.helper_netiface_interface()
        netifaces.AF_INET = 2
        with patch('nmoscommon.interfaceController.nmoscommonconfig') as config:
            config.config = {"interfaces": ["eno1"]}
            expected = ["192.168.0.5"]
            actual = self.dut._get_default_interface_from_file()
            self.assertEqual(actual, expected)

    @patch('nmoscommon.interfaceController.netifaces')
    def test_get_default_interface_from_gateway(self, netifaces):
        """Check the controller can automatically find the default interface using netifaces"""
        netifaces.gateways = self.helper_netiface_gateways()
        netifaces.ifaddresses = self.helper_netiface_interface()
        netifaces.AF_INET = 2
        actual = self.dut._get_default_interface_from_gateway()
        expected = ["192.168.0.2"]
        self.assertEqual(actual, expected)

    @patch('nmoscommon.interfaceController.netifaces')
    def test_get_default_all_interface(self, netifaces):
        """Check the controller can fall back to getting all interfaces"""
        netifaces.ifaddresses = self.helper_netiface_interface()
        netifaces.AF_INET = 2
        netifaces.interfaces.return_value = ["eno1", "ens4f0"]
        expected = ["192.168.0.5", "192.168.0.4"]
        actual = self.dut._get_all_interfaces()
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

    @patch("netifaces.ifaddresses")
    @patch("netifaces.interfaces")
    def test_get_all_interfaces(self, interfaces, ifaddresses):
        interfaces.return_value = [sentinel.if0, sentinel.if1, sentinel.if2, ]
        addresses = {
            sentinel.if0: {netifaces.AF_INET: [{'addr': sentinel.if0_AF_INET_0_addr},
                                               {'addr': sentinel.if0_AF_INET_1_addr}]},
            sentinel.if1: {netifaces.AF_INET: [{'addr': sentinel.if1_AF_INET_0_addr},
                                               {'addr': sentinel.if1_AF_INET_1_addr}]},
            sentinel.if2: {netifaces.AF_INET: [{'addr': sentinel.if2_AF_INET_0_addr},
                                               {'addr': sentinel.if2_AF_INET_1_addr}]},
            }
        ifaddresses.side_effect = lambda x: addresses[x]
        self.assertEqual(self.dut._get_all_interfaces(), [
                                                            sentinel.if0_AF_INET_0_addr,
                                                            sentinel.if1_AF_INET_0_addr,
                                                            sentinel.if2_AF_INET_0_addr])

    @patch("netifaces.ifaddresses")
    @patch("netifaces.interfaces")
    def test_get_all_interfaces__ignores_loopback(self, interfaces, ifaddresses):
        interfaces.return_value = ["lo", sentinel.if1, sentinel.if2, ]
        addresses = {
            "lo": {netifaces.AF_INET: [{'addr': sentinel.if0_AF_INET_0_addr},
                                       {'addr': sentinel.if0_AF_INET_1_addr}]},
            sentinel.if1: {netifaces.AF_INET: [{'addr': sentinel.if1_AF_INET_0_addr},
                                               {'addr': sentinel.if1_AF_INET_1_addr}]},
            sentinel.if2: {netifaces.AF_INET: [{'addr': sentinel.if2_AF_INET_0_addr},
                                               {'addr': sentinel.if2_AF_INET_1_addr}]},
            }
        ifaddresses.side_effect = lambda x: addresses[x]
        self.assertEqual(self.dut._get_all_interfaces(), [sentinel.if1_AF_INET_0_addr, sentinel.if2_AF_INET_0_addr])

    @patch("netifaces.ifaddresses")
    @patch("netifaces.interfaces")
    def test_get_all_interfaces__ignores_loopback_with_number(self, interfaces, ifaddresses):
        interfaces.return_value = ["lo0", sentinel.if1, sentinel.if2, ]
        addresses = {
            "lo": {netifaces.AF_INET: [{'addr': sentinel.if0_AF_INET_0_addr},
                                       {'addr': sentinel.if0_AF_INET_1_addr}]},
            sentinel.if1: {netifaces.AF_INET: [{'addr': sentinel.if1_AF_INET_0_addr},
                                               {'addr': sentinel.if1_AF_INET_1_addr}]},
            sentinel.if2: {netifaces.AF_INET: [{'addr': sentinel.if2_AF_INET_0_addr},
                                               {'addr': sentinel.if2_AF_INET_1_addr}]},
            }
        ifaddresses.side_effect = lambda x: addresses[x]
        self.assertEqual(self.dut._get_all_interfaces(), [sentinel.if1_AF_INET_0_addr, sentinel.if2_AF_INET_0_addr])

    @patch("netifaces.ifaddresses")
    @patch("netifaces.interfaces")
    def test_get_all_interfaces__ignores_linklocal_address(self, interfaces, ifaddresses):
        interfaces.return_value = [sentinel.if0, sentinel.if1, sentinel.if2, ]
        addresses = {
            sentinel.if0: {netifaces.AF_INET: [{'addr': "127.0.0.1"},
                                               {'addr': sentinel.if0_AF_INET_1_addr}]},
            sentinel.if1: {netifaces.AF_INET: [{'addr': sentinel.if1_AF_INET_0_addr},
                                               {'addr': sentinel.if1_AF_INET_1_addr}]},
            sentinel.if2: {netifaces.AF_INET: [{'addr': sentinel.if2_AF_INET_0_addr},
                                               {'addr': sentinel.if2_AF_INET_1_addr}]},
            }
        ifaddresses.side_effect = lambda x: addresses[x]
        self.assertEqual(self.dut._get_all_interfaces(), [sentinel.if1_AF_INET_0_addr, sentinel.if2_AF_INET_0_addr])

    @patch("netifaces.ifaddresses")
    @patch("netifaces.interfaces")
    def test_get_all_interfaces__skips_non_IPv4(self, interfaces, ifaddresses):
        interfaces.return_value = [sentinel.if0, sentinel.if1, sentinel.if2, ]
        addresses = {
            sentinel.if0: {netifaces.AF_INET6: [{'addr': sentinel.if0_AF_INET_0_addr},
                                                {'addr': sentinel.if0_AF_INET_1_addr}]},
            sentinel.if1: {netifaces.AF_INET: [{'addr': sentinel.if1_AF_INET_0_addr},
                                               {'addr': sentinel.if1_AF_INET_1_addr}]},
            sentinel.if2: {netifaces.AF_INET: [{'addr': sentinel.if2_AF_INET_0_addr},
                                               {'addr': sentinel.if2_AF_INET_1_addr}]},
            }
        ifaddresses.side_effect = lambda x: addresses[x]
        self.assertEqual(self.dut._get_all_interfaces(), [sentinel.if1_AF_INET_0_addr, sentinel.if2_AF_INET_0_addr])

    @patch("netifaces.ifaddresses")
    @patch("netifaces.interfaces")
    def test_get_all_interfaces__skips_empty_IPv4(self, interfaces, ifaddresses):
        interfaces.return_value = [sentinel.if0, sentinel.if1, sentinel.if2, ]
        addresses = {
            sentinel.if0: {netifaces.AF_INET: []},
            sentinel.if1: {netifaces.AF_INET: [{'addr': sentinel.if1_AF_INET_0_addr},
                                               {'addr': sentinel.if1_AF_INET_1_addr}]},
            sentinel.if2: {netifaces.AF_INET: [{'addr': sentinel.if2_AF_INET_0_addr},
                                               {'addr': sentinel.if2_AF_INET_1_addr}]},
            }
        ifaddresses.side_effect = lambda x: addresses[x]
        self.assertEqual(self.dut._get_all_interfaces(), [sentinel.if1_AF_INET_0_addr, sentinel.if2_AF_INET_0_addr])

    @patch("netifaces.ifaddresses")
    @patch("netifaces.interfaces")
    def test_get_all_interfaces__returns_false_when_no_interface(self, interfaces, ifaddresses):
        interfaces.return_value = []
        self.assertFalse(self.dut._get_all_interfaces())

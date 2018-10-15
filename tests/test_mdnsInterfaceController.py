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
from mock import MagicMock, patch


class TestMDNSInterfaceController(unittest.TestCase):

    def setUp(self):
        self.dut = MDNSInterfaceController()

    """Check the controller can automatically find the default interface using netifaces"""
    def test_find_default_interface(self):
        with patch('nmoscommon.mdns.mdnsInterfaceController.netifaces') as netifaces:
            self.dut.addInterface = MagicMock()
            netifaces.gateways = self.helper_netiface_gateways()
            netifaces.ifaddresses = self.helper_netiface_interface()
            netifaces.AF_INET = 2
            self.dut.addInterface = MagicMock()
            self.dut._findDefaultInterface()
            actual = self.dut.addInterface.call_args[0][0]
            expected = "192.168.0.5"
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
            returnValue = {17: [{'broadcast': u'ff:ff:ff:ff:ff:ff', 'addr': u'64:51:06:2a:d8:9a'}],
                           2: [{'broadcast': u'192.168.0.255', 'netmask': u'255.255.255.0', 'addr': u'192.168.0.5'}],
                           10: [{'netmask': u'ffff:ffff:ffff:ffff::/64', 'addr': u'fe80::6651:6ff:fe2a:d89a%eno1'}]}
            if interface == "eno1":
                return returnValue
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
        expected = self.dut.defaultInterface = "default"
        actual = self.dut.getInterfaces([])
        self.assertEqual([expected], actual)

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

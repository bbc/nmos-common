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

    def test_add_interface(self):
        """Check that adding duplicate interfaces does not produce a duplicate listing"""
        with patch('nmoscommon.mdns.mdnsInterfaceController.MDNSInterface') as interface:
            self.dut.interfaces = {}
            ret = MagicMock()
            interface.return_value = ret
            self.dut.addInterface("192.168.0.5")
            self.assertEqual(self.dut.interfaces, {"192.168.0.5": ret})
            self.dut.addInterface("192.168.0.5")
            self.assertEqual(self.dut.interfaces, {"192.168.0.5": ret})

    def test_get_interfaces(self):
        """Check interfaces can be retrieved"""
        expected = self.dut.defaultInterfaces = ["default"]
        actual = self.dut.getInterfaces([])
        self.assertEqual(expected, actual)

        self.dut.addInterface = MagicMock(side_effect=range(0, 5))
        actual = self.dut.getInterfaces(["a", "b", "c", "d", "e"])
        self.assertEqual(actual, list(range(0, 5)))

    def test_close(self):
        """Test the class shuts all its interfaces correctly"""
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

    def test_set_default_interfaces(self):
        """Check that the default interfaces added"""
        with patch('nmoscommon.mdns.mdnsInterfaceController.MDNSInterface') as mdns:
            with patch('nmoscommon.mdns.mdnsInterfaceController.InterfaceController') as interface:
                self.dut.interfaces = {}
                ret = MagicMock()
                mdns.return_value = ret
                interface.return_value.get_default_interfaces.return_value = ['192.168.0.5']
                self.dut._set_default_interfaces()

                self.assertEqual(self.dut.interfaces, {"192.168.0.5": ret})

    def test_set_default_interfaces__raises_exception(self):
        """Check that when no default interfaces are found, an exception is raised"""
        with patch('nmoscommon.mdns.mdnsInterfaceController.InterfaceController') as interface:
            with self.assertRaises(NoNetworkInterfacesFoundException):
                interface.return_value.get_default_interfaces.return_value = []
                self.dut._set_default_interfaces()


if __name__ == "__main__":
    unittest.main()

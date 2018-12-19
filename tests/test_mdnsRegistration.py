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
from nmoscommon.mdns.mdnsRegistration import MDNSRegistration
from mock import MagicMock, patch
from socket import inet_aton


class TestMDNSRegistration(unittest.TestCase):

    def setUp(self):
        self.name = "testName"
        self.regType = "_nmos-test._tcp"
        self.port = 8080,
        self.txtRecord = {}
        self.interface = self.build_mock_interface()
        self.dut = self.build_dut()

    def build_dut(self):
        dut = MDNSRegistration(
            [self.interface],
            self.name,
            self.regType,
            self.port,
            self.txtRecord
        )
        dut.info = {"192.168.0.5": "testInfo"}
        return dut

    def build_mock_interface(self):
        interface = MagicMock()
        interface.register_service = MagicMock()
        interface.unregister_service = MagicMock()
        interface.ip = "192.168.0.5"
        return interface

    """Test registrations are added to the interface correctly"""
    def test_registration(self):
        with patch('nmoscommon.mdns.mdnsRegistration.ServiceInfo') as info:
            self.dut = self.build_dut()
            regFunc = MagicMock()
            for interface in self.dut.interfaces:
                interface.registerService = regFunc
            self.dut.register()
            self.assertTrue(regFunc.called)
            argv, kwargs = info.call_args
        expectedKwargs = {
            "port": self.port,
            "properties": self.txtRecord,
            "address": inet_aton(self.interface.ip)
        }
        self.assertDictEqual(expectedKwargs, kwargs)
        expectedArgv = (
            self.regType + '.local.',
            self.name + "." + self.regType + '.local.'
        )
        self.assertEqual(argv, expectedArgv)

    """Test registrations are removed from the interfaces correctly"""
    def test_unregister(self):
        unregFunc = self.dut.interfaces[0].unregisterService = MagicMock()
        self.dut.info = {"192.168.0.5": None}
        self.dut.unRegister()
        self.assertTrue(unregFunc.called)

    """Test the method that creates unique service names for each interface"""
    def test_make_unique(self):
        self.dut.interfaces = [
            MagicMock(),
            MagicMock()
        ]
        self.dut.interfaces[0].ip = "192.168.0.1"
        self.dut.interfaces[1].ip = "192.168.10.1"
        actual = self.dut._makeNamesUnique()
        expected = {
            "192.168.0.1": self.name + "_192-168-0-1",
            "192.168.10.1": self.name + "_192-168-10-1"
        }
        self.assertEqual(actual, expected)

    def test_unregiester_on_update(self):
        self.dut.info = {"192.168.0.5": "info"}
        self.dut.update(port=999)
        self.assertTrue(self.dut.interfaces[0].unregisterService.called)
        expected = "info"
        actual = self.dut.interfaces[0].unregisterService.call_args
        self.assertEqual(actual[0][0], expected)

    def test_update_name(self):
        self.dut.update(name="main")
        self.assertEqual(self.dut.name, "main")

    def test_update_port(self):
        self.dut.update(port=999)
        self.assertEqual(self.dut.port, 999)

    def test_update_type(self):
        self.dut.update(regtype="_newtype._tcp")
        self.assertEqual(self.dut.regtype, "_newtype._tcp")

    def test_update_txt(self):
        self.dut.update(txtRecord={"text": "yes"})
        self.assertEqual(self.dut.txtRecord, {"text": "yes"})

    def test_conform_txt(self):
        testObject = {
            "int": 200,
            "boolean": True,
            "string": "world"
        }
        expected = {
            "int": "200",
            "boolean": "True",
            "string": "world"
        }
        actual = self.dut._conformTxtRecord(testObject)
        self.assertDictEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()

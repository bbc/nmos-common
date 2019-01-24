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
from nmoscommon.mdns.mdnsListener import MDNSListener
from mock import MagicMock
import socket


class TestMDNSListener(unittest.TestCase):

    def setUp(self):
        self.callback = MagicMock()
        self.dut = MDNSListener(self.callback, False)
        self.address = "192.168.0.1"
        self.port = 8080
        self.txt = {}
        self.type = "nmos-test._tcp.local."
        self.name = "name_" + self.type
        self.hostname = self.name.rstrip(".")
        self.server = self.name

    def helper_build_info(self):
        info = MagicMock()
        info.address = socket.inet_aton(self.address)
        info.port = self.port
        info.type = self.type
        info.name = self.name
        info.server = self.server
        info.properties = {}
        return info

    """Test adding a service when none is already present"""
    def test_add_service_empty(self):
        self.helper_add_service()

    """Test adding a service when one is already present of the smae type"""
    def test_add_service_existing(self):
        self.dut.records = {
            self.type: {
                "otherName": "otherInfo"
            }
        }
        self.helper_add_service()

    def helper_build_expected_callback(self, action):
        return {
            "action": action,
            "name": self.name,
            "type": self.type,
            "port": self.port,
            "address": self.address,
            "hostname": self.hostname,
            "txt": {}
        }

    def helper_add_service(self):
        zeroconf = MagicMock()
        getService = zeroconf.get_service_info = MagicMock()
        getService.return_value = self.helper_build_info()
        self.dut.add_service(zeroconf, self.type, self.name)
        self.assertTrue(self.callback.called)
        argv, vargs = self.callback.call_args
        actual = argv[0]
        expected = self.helper_build_expected_callback("add")
        self.assertDictEqual(actual, expected)

    """Test we are not notified of removals in register only mode"""
    def test_remove_service_reg_only(self):
        self.dut = MDNSListener(self.callback, True)
        self.helper_remove_service()
        self.assertFalse(self.callback.called)

    """Test correct removals callback when not in register only mode"""
    def test_remove_service(self):
        self.helper_remove_service()
        argv, vargs = self.callback.call_args
        actual = argv[0]
        expected = self.helper_build_expected_callback("remove")
        self.assertEqual(actual, expected)

    def helper_remove_service(self):
        self.dut.records[self.type] = {}
        self.dut.records[self.type][self.name] = self.helper_build_info()
        self.dut.remove_service(None, self.type, self.name)


if __name__ == "__main__":
    unittest.main()
